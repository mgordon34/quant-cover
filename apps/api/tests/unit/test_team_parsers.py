import json
from pathlib import Path

import pytest

from quant_cover_api.scraping.parsers.nba_com_teams import parse_nba_com_teams
from quant_cover_api.scraping.parsers.teams import extract_team_code, parse_stathead_teams

FIXTURES_DIR = Path(__file__).resolve().parents[2] / "src/quant_cover_api/scraping/fixtures"


def test_extract_team_code_returns_uppercase_abbreviation() -> None:
    assert extract_team_code("/teams/bos/2025.html") == "BOS"


def test_extract_team_code_returns_empty_string_for_non_team_path() -> None:
    assert extract_team_code("/players/j/jamesle01.html") == ""


def test_parse_stathead_teams_reads_expected_fixture_rows() -> None:
    html = (FIXTURES_DIR / "stathead_nba_teams.html").read_text()

    teams = parse_stathead_teams(html)

    assert len(teams) == 30
    assert teams[0].abbreviation == "ATL"
    assert teams[0].name == "Atlanta Hawks"
    assert any(team.abbreviation == "BOS" and team.name == "Boston Celtics" for team in teams)


def test_parse_stathead_teams_raises_when_active_table_is_missing() -> None:
    with pytest.raises(ValueError, match="could not find active teams table"):
        parse_stathead_teams("<html></html>")


def test_parse_nba_com_teams_reads_expected_fixture_rows() -> None:
    payload = json.loads((FIXTURES_DIR / "nba_com_nba_teams.json").read_text())

    teams = parse_nba_com_teams(payload)

    assert len(teams) == 30
    assert any(team.abbreviation == "OKC" and team.name == "Oklahoma City Thunder" for team in teams)
    assert any(team.abbreviation == "LAL" and team.name == "Los Angeles Lakers" for team in teams)


def test_parse_nba_com_teams_raises_when_scoreboard_has_no_games() -> None:
    with pytest.raises(ValueError, match="no games found in nba.com payload"):
        parse_nba_com_teams({"scoreboard": {"games": []}})

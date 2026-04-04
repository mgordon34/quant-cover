from quant_cover_api.scraping.parsers.teams import ParsedTeam


def parse_nba_com_teams(payload: dict) -> list[ParsedTeam]:
    if "teams" in payload:
        teams = [_parse_fixture_team(team) for team in payload["teams"]]
        return _dedupe_teams(teams)

    games = payload.get("scoreboard", {}).get("games", [])
    if not games:
        raise ValueError("no games found in nba.com payload")

    parsed_teams: list[ParsedTeam] = []
    for game in games:
        for team_key in ("homeTeam", "awayTeam"):
            team = game.get(team_key, {})
            parsed_team = _parse_scoreboard_team(team)
            if parsed_team is not None:
                parsed_teams.append(parsed_team)

    teams = _dedupe_teams(parsed_teams)
    if not teams:
        raise ValueError("no teams found in nba.com payload")
    return teams


def _parse_fixture_team(team: dict) -> ParsedTeam:
    abbreviation = str(team.get("teamTricode", "")).strip().upper()
    city = str(team.get("teamCity", "")).strip()
    name = str(team.get("teamName", "")).strip()
    full_name = " ".join(part for part in (city, name) if part)
    if not abbreviation or not full_name:
        raise ValueError("fixture team payload is missing required fields")
    return ParsedTeam(abbreviation=abbreviation, name=full_name)


def _parse_scoreboard_team(team: dict) -> ParsedTeam | None:
    abbreviation = str(team.get("teamTricode", "")).strip().upper()
    city = str(team.get("teamCity", "")).strip()
    name = str(team.get("teamName", "")).strip()
    full_name = " ".join(part for part in (city, name) if part)
    if not abbreviation or not full_name:
        return None
    return ParsedTeam(abbreviation=abbreviation, name=full_name)


def _dedupe_teams(teams: list[ParsedTeam]) -> list[ParsedTeam]:
    deduped: dict[str, ParsedTeam] = {}
    for team in teams:
        deduped[team.abbreviation] = team
    return list(deduped.values())

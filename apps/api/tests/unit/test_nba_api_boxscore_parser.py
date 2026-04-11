from decimal import Decimal

import pytest

from quant_cover_api.scraping.parsers.nba_api_boxscore import parse_nba_api_boxscore


def test_parse_nba_api_boxscore_reads_expected_player_rows() -> None:
    payload = {
        "traditional": {
            "boxScoreTraditional": {
                "gameId": "0022501114",
                "homeTeam": {
                    "teamTricode": "CHA",
                    "players": [
                        {
                            "personId": 1,
                            "firstName": "LaMelo",
                            "familyName": "Ball",
                            "position": "G",
                            "statistics": {
                                "minutes": "25:10",
                                "points": 15,
                                "reboundsTotal": 2,
                                "assists": 11,
                                "threePointersMade": 2,
                                "steals": 1,
                                "blocks": 0,
                                "turnovers": 0,
                            },
                        },
                        {
                            "personId": 2,
                            "firstName": "Xavier",
                            "familyName": "Tillman",
                            "position": "",
                            "comment": "DNP - Coach's Decision",
                            "statistics": {
                                "minutes": "",
                                "points": 0,
                                "reboundsTotal": 0,
                                "assists": 0,
                                "threePointersMade": 0,
                                "steals": 0,
                                "blocks": 0,
                                "turnovers": 0,
                            },
                        },
                    ],
                },
                "awayTeam": {
                    "teamTricode": "PHX",
                    "players": [
                        {
                            "personId": 3,
                            "firstName": "Devin",
                            "familyName": "Booker",
                            "position": "G",
                            "statistics": {
                                "minutes": "37:30",
                                "points": 28,
                                "reboundsTotal": 5,
                                "assists": 7,
                                "threePointersMade": 3,
                                "steals": 2,
                                "blocks": 1,
                                "turnovers": 4,
                            },
                        }
                    ],
                },
            }
        },
        "advanced": {
            "boxScoreAdvanced": {
                "gameId": "0022501114",
                "homeTeam": {
                    "teamTricode": "CHA",
                    "players": [
                        {
                            "personId": 1,
                            "statistics": {
                                "offensiveRating": 154.9,
                                "defensiveRating": 129.4,
                            },
                        }
                    ],
                },
                "awayTeam": {
                    "teamTricode": "PHX",
                    "players": [
                        {
                            "personId": 3,
                            "statistics": {
                                "offensiveRating": 118.2,
                                "defensiveRating": 121.6,
                            },
                        }
                    ],
                },
            }
        },
    }

    rows = parse_nba_api_boxscore(payload)

    assert len(rows) == 2
    assert rows[0].source_game_id == "0022501114"
    assert rows[0].source_player_id == "1"
    assert rows[0].full_name == "LaMelo Ball"
    assert rows[0].team_code == "CHA"
    assert rows[0].opponent_team_code == "PHX"
    assert rows[0].minutes == Decimal("25.17")
    assert rows[0].points == 15
    assert rows[0].offensive_rating == Decimal("154.9")
    assert rows[1].source_player_id == "3"
    assert rows[1].team_code == "PHX"


def test_parse_nba_api_boxscore_raises_for_mismatched_game_ids() -> None:
    payload = {
        "traditional": {
            "boxScoreTraditional": {
                "gameId": "1",
                "homeTeam": {"teamTricode": "CHA", "players": []},
                "awayTeam": {"teamTricode": "PHX", "players": []},
            }
        },
        "advanced": {"boxScoreAdvanced": {"gameId": "2", "homeTeam": {"players": []}, "awayTeam": {"players": []}}},
    }

    with pytest.raises(ValueError, match="mismatched game ids"):
        parse_nba_api_boxscore(payload)

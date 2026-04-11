from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Any


@dataclass(frozen=True)
class ParsedPlayerBoxscore:
    source_game_id: str
    source_player_id: str | None
    full_name: str
    display_name: str
    primary_position: str | None
    team_code: str
    opponent_team_code: str
    started: bool | None
    minutes: Decimal | None
    points: int | None
    rebounds: int | None
    assists: int | None
    threes_made: int | None
    steals: int | None
    blocks: int | None
    turnovers: int | None
    offensive_rating: Decimal | None
    defensive_rating: Decimal | None
    source_row_id: str | None = None


def parse_nba_api_boxscore(payload: dict[str, Any]) -> list[ParsedPlayerBoxscore]:
    traditional = payload.get("traditional", {}).get("boxScoreTraditional")
    advanced = payload.get("advanced", {}).get("boxScoreAdvanced")
    if not traditional or not advanced:
        raise ValueError("nba_api boxscore payload must include traditional and advanced boxscore data")

    traditional_game_id = str(traditional.get("gameId", "")).strip()
    advanced_game_id = str(advanced.get("gameId", "")).strip()
    if not traditional_game_id or not advanced_game_id:
        raise ValueError("nba_api boxscore payload is missing game id")
    if traditional_game_id != advanced_game_id:
        raise ValueError("nba_api boxscore payload has mismatched game ids")

    parsed_rows: list[ParsedPlayerBoxscore] = []
    for team_side, opponent_side in (("homeTeam", "awayTeam"), ("awayTeam", "homeTeam")):
        traditional_team = traditional.get(team_side) or {}
        opponent_team = traditional.get(opponent_side) or {}
        advanced_team = advanced.get(team_side) or {}

        team_code = str(traditional_team.get("teamTricode", "")).strip().upper()
        opponent_team_code = str(opponent_team.get("teamTricode", "")).strip().upper()
        if not team_code or not opponent_team_code:
            raise ValueError("nba_api boxscore payload is missing team codes")

        advanced_by_player_id = {
            str(player.get("personId")): player.get("statistics") or {}
            for player in advanced_team.get("players", [])
            if player.get("personId") not in (None, "")
        }
        starter_ids = _starter_player_ids(traditional_team.get("players", []))

        for player in traditional_team.get("players", []):
            source_player_id = _parse_source_player_id(player.get("personId"))
            if source_player_id is None:
                continue

            statistics = player.get("statistics") or {}
            minutes = _parse_minutes(statistics.get("minutes"))
            if minutes is None:
                continue

            full_name = _parse_full_name(player)
            if not full_name:
                continue

            advanced_statistics = advanced_by_player_id.get(source_player_id, {})
            parsed_rows.append(
                ParsedPlayerBoxscore(
                    source_game_id=traditional_game_id,
                    source_player_id=source_player_id,
                    full_name=full_name,
                    display_name=full_name,
                    primary_position=_parse_optional_string(player.get("position")),
                    team_code=team_code,
                    opponent_team_code=opponent_team_code,
                    started=source_player_id in starter_ids if starter_ids else None,
                    minutes=minutes,
                    points=_parse_int(statistics.get("points")),
                    rebounds=_parse_int(statistics.get("reboundsTotal")),
                    assists=_parse_int(statistics.get("assists")),
                    threes_made=_parse_int(statistics.get("threePointersMade")),
                    steals=_parse_int(statistics.get("steals")),
                    blocks=_parse_int(statistics.get("blocks")),
                    turnovers=_parse_int(statistics.get("turnovers")),
                    offensive_rating=_parse_decimal(advanced_statistics.get("offensiveRating")),
                    defensive_rating=_parse_decimal(advanced_statistics.get("defensiveRating")),
                )
            )

    if not parsed_rows:
        raise ValueError("no player boxscore rows found in nba_api boxscore payload")

    return parsed_rows


def _starter_player_ids(players: list[dict[str, Any]]) -> set[str]:
    starter_ids: list[str] = []
    for player in players:
        source_player_id = _parse_source_player_id(player.get("personId"))
        if source_player_id is None:
            continue
        minutes = _parse_minutes((player.get("statistics") or {}).get("minutes"))
        if minutes is None:
            continue
        starter_ids.append(source_player_id)
        if len(starter_ids) == 5:
            break
    return set(starter_ids)


def _parse_source_player_id(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value).strip()


def _parse_full_name(player: dict[str, Any]) -> str:
    first_name = _parse_optional_string(player.get("firstName"))
    family_name = _parse_optional_string(player.get("familyName"))
    full_name = " ".join(part for part in (first_name, family_name) if part)
    return full_name.strip()


def _parse_optional_string(value: Any) -> str | None:
    if value in (None, ""):
        return None
    text = str(value).strip()
    return text or None


def _parse_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


def _parse_decimal(value: Any) -> Decimal | None:
    if value in (None, ""):
        return None
    return Decimal(str(value))


def _parse_minutes(value: Any) -> Decimal | None:
    if value in (None, ""):
        return None

    raw_value = str(value).strip()
    if not raw_value:
        return None
    if ":" not in raw_value:
        return Decimal(raw_value)

    minutes_text, seconds_text = raw_value.split(":", maxsplit=1)
    total_seconds = (int(minutes_text) * 60) + int(seconds_text)
    return (Decimal(total_seconds) / Decimal(60)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

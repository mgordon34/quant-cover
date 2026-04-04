from dataclasses import dataclass
from datetime import date, datetime
from typing import Any


@dataclass(frozen=True)
class ParsedGame:
    source_game_id: str
    game_date: date
    started_at: datetime | None
    status: str
    home_team_code: str
    away_team_code: str
    home_score: int | None
    away_score: int | None
    season: str | None = None
    season_type: str | None = None


def parse_nba_api_games(payload: dict[str, Any]) -> list[ParsedGame]:
    games = payload.get("scoreboard", {}).get("games", [])
    if not games:
        return []

    parsed_games: list[ParsedGame] = []
    for game in games:
        source_game_id = str(game.get("gameId", "")).strip()
        home_team_code = str(game.get("homeTeam", {}).get("teamTricode", "")).strip().upper()
        away_team_code = str(game.get("awayTeam", {}).get("teamTricode", "")).strip().upper()
        if not source_game_id or not home_team_code or not away_team_code:
            continue

        parsed_games.append(
            ParsedGame(
                source_game_id=source_game_id,
                game_date=_parse_game_date(payload, game),
                started_at=_parse_datetime(game.get("gameTimeUTC")),
                status=_map_game_status(game),
                home_team_code=home_team_code,
                away_team_code=away_team_code,
                home_score=_parse_int(game.get("homeTeam", {}).get("score")),
                away_score=_parse_int(game.get("awayTeam", {}).get("score")),
            )
        )

    if not parsed_games:
        raise ValueError("no valid games found in nba_api games payload")

    return parsed_games


def _parse_game_date(payload: dict[str, Any], game: dict[str, Any]) -> date:
    raw_value = game.get("gameDate") or payload.get("scoreboard", {}).get("gameDate") or game.get("gameTimeUTC")
    if raw_value is None:
        raise ValueError("game payload is missing game date")
    return datetime.fromisoformat(str(raw_value).replace("Z", "+00:00")).date()


def _parse_datetime(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _parse_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


def _map_game_status(game: dict[str, Any]) -> str:
    status_code = game.get("gameStatus")
    status_text = str(game.get("gameStatusText", "")).strip().lower()

    if status_code == 1 or status_text in {"scheduled", "pre game", "pregame"}:
        return "scheduled"
    if status_code == 2 or "halftime" in status_text or "qtr" in status_text or "progress" in status_text:
        return "in_progress"
    if status_code == 3 or status_text == "final":
        return "completed"
    if "postponed" in status_text:
        return "postponed"
    if "cancelled" in status_text or "canceled" in status_text:
        return "cancelled"

    raise ValueError(f"unsupported nba_api game status: code={status_code} text={status_text}")

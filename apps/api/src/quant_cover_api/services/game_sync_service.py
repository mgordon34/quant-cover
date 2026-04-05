import logging
import time
from datetime import date, timedelta
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from quant_cover_api.db.models.game import Game
from quant_cover_api.db.models.league import League
from quant_cover_api.db.models.team import Team
from quant_cover_api.scraping.clients.nba_api_client import NbaApiClient
from quant_cover_api.scraping.parsers.nba_api_games import ParsedGame, parse_nba_api_games
from quant_cover_api.services.sync_result import SyncResult

logger = logging.getLogger(__name__)


class GameSyncService:
    def __init__(self, *, session: Session, nba_api_client: NbaApiClient | None = None) -> None:
        self.session = session
        self.nba_api_client = nba_api_client

    def sync_nba_api_games_for_date(self, *, league_key: str, game_date: date, fixture_path: Path | None = None) -> SyncResult:
        logger.info(f"starting game scrape for date league={league_key} date={game_date.isoformat()}")
        league = self._get_league(league_key)
        if self.nba_api_client is None:
            raise ValueError("nba_api client is not configured")

        payload = self.nba_api_client.fetch_games_payload(
            league_key=league_key,
            game_date=game_date,
            fixture_path=fixture_path,
        )
        parsed_games = parse_nba_api_games(payload)
        result = self._sync_parsed_games(league=league, parsed_games=parsed_games)
        logger.info(
            f"finished game scrape for date league={league_key} date={game_date.isoformat()} "
            f"games_scraped={len(parsed_games)} created={result.created} "
            f"updated={result.updated} skipped={result.skipped}"
        )
        return result

    def sync_nba_api_games_for_date_range(
        self,
        *,
        league_key: str,
        start_date: date,
        end_date: date,
        request_delay_seconds: float = 1.0,
    ) -> SyncResult:
        if end_date < start_date:
            raise ValueError("end_date must be on or after start_date")

        result = SyncResult()
        current_date = start_date
        while current_date <= end_date:
            daily_result = self.sync_nba_api_games_for_date(league_key=league_key, game_date=current_date)
            result.created += daily_result.created
            result.updated += daily_result.updated
            result.skipped += daily_result.skipped

            if current_date < end_date:
                time.sleep(request_delay_seconds)

            current_date += timedelta(days=1)

        return result

    def _sync_parsed_games(self, *, league: League, parsed_games: list[ParsedGame]) -> SyncResult:
        result = SyncResult()

        for parsed_game in parsed_games:
            home_team = self._get_team(league_id=league.id, abbreviation=parsed_game.home_team_code)
            away_team = self._get_team(league_id=league.id, abbreviation=parsed_game.away_team_code)

            game = self.session.scalar(
                select(Game).where(
                    Game.league_id == league.id,
                    Game.stathead_game_id == parsed_game.source_game_id,
                )
            )

            # If no game is present, add new game
            if game is None:
                self.session.add(
                    Game(
                        league_id=league.id,
                        season=parsed_game.season,
                        season_type=parsed_game.season_type,
                        game_date=parsed_game.game_date,
                        started_at=parsed_game.started_at,
                        status=parsed_game.status,
                        home_team_id=home_team.id,
                        away_team_id=away_team.id,
                        home_score=parsed_game.home_score,
                        away_score=parsed_game.away_score,
                        stathead_game_id=parsed_game.source_game_id,
                    )
                )
                result.created += 1
                continue

            changed = False
            for attr, value in (
                ("season", parsed_game.season),
                ("season_type", parsed_game.season_type),
                ("game_date", parsed_game.game_date),
                ("started_at", parsed_game.started_at),
                ("status", parsed_game.status),
                ("home_team_id", home_team.id),
                ("away_team_id", away_team.id),
                ("home_score", parsed_game.home_score),
                ("away_score", parsed_game.away_score),
            ):
                if getattr(game, attr) != value:
                    setattr(game, attr, value)
                    changed = True

            if changed:
                result.updated += 1
            else:
                result.skipped += 1

        self.session.commit()
        return result

    def _get_league(self, league_key: str) -> League:
        league = self.session.scalar(select(League).where(League.key == league_key))
        if league is None:
            raise ValueError(f"league not found: {league_key}")
        return league

    def _get_team(self, *, league_id: int, abbreviation: str) -> Team:
        team = self.session.scalar(select(Team).where(Team.league_id == league_id, Team.abbreviation == abbreviation))
        if team is None:
            raise ValueError(f"team not found for league_id={league_id} abbreviation={abbreviation}")
        return team

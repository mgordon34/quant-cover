import logging
import time
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from quant_cover_api.db.models.game import Game
from quant_cover_api.db.models.league import League
from quant_cover_api.db.models.player_game_stat import PlayerGameStat
from quant_cover_api.db.models.team import Team
from quant_cover_api.scraping.clients.nba_api_client import NbaApiClient
from quant_cover_api.scraping.parsers.nba_api_boxscore import ParsedPlayerBoxscore, parse_nba_api_boxscore
from quant_cover_api.services.player_resolution_service import PlayerResolutionService
from quant_cover_api.services.sync_result import SyncResult

logger = logging.getLogger(__name__)


class BoxscoreSyncService:
    def __init__(
        self,
        *,
        session: Session,
        nba_api_client: NbaApiClient | None = None,
        player_resolution_service: PlayerResolutionService | None = None,
    ) -> None:
        self.session = session
        self.nba_api_client = nba_api_client
        self.player_resolution_service = player_resolution_service or PlayerResolutionService(session=session)

    def sync_nba_api_boxscores_for_date_range(
        self,
        *,
        league_key: str,
        start_date: date,
        end_date: date,
        request_delay_seconds: float = 1.0,
    ) -> SyncResult:
        if end_date < start_date:
            raise ValueError("end_date must be on or after start_date")

        logger.info(
            f"starting boxscore scrape for date range league={league_key} "
            f"from_date={start_date.isoformat()} to_date={end_date.isoformat()}"
        )
        league = self._get_league(league_key)
        result = SyncResult()
        current_date = start_date
        games: list[Game] = []
        while current_date <= end_date:
            games.extend(self._get_completed_games_for_date(league_id=league.id, game_date=current_date))
            current_date += timedelta(days=1)

        if not games:
            logger.info(
                f"finished boxscore scrape for date range league={league_key} "
                f"from_date={start_date.isoformat()} to_date={end_date.isoformat()} games_scraped=0 created=0 updated=0 skipped=0"
            )
            return result

        result = self._sync_games_with_delay(
            league=league,
            league_key=league_key,
            games=games,
            request_delay_seconds=request_delay_seconds,
        )
        logger.info(
            f"finished boxscore scrape for date range league={league_key} "
            f"from_date={start_date.isoformat()} to_date={end_date.isoformat()} "
            f"games_scraped={len(games)} created={result.created} updated={result.updated} skipped={result.skipped}"
        )
        return result

    def _sync_games_with_delay(
        self,
        *,
        league: League,
        league_key: str,
        games: list[Game],
        request_delay_seconds: float = 1.0,
    ) -> SyncResult:
        result = SyncResult()
        for index, game in enumerate(games):
            logger.info(
                f"syncing boxscore game {index + 1}/{len(games)} "
                f"source_game_id={game.source_game_id} date={game.game_date.isoformat()}"
            )
            game_result = self._sync_game_boxscore(league=league, league_key=league_key, game=game)
            result.created += game_result.created
            result.updated += game_result.updated
            result.skipped += game_result.skipped

            if index < len(games) - 1:
                logger.info(f"sleeping between boxscore requests seconds={request_delay_seconds}")
                time.sleep(request_delay_seconds)

        return result

    def _get_completed_games_for_date(self, *, league_id: int, game_date: date) -> list[Game]:
        return list(
            self.session.scalars(
                select(Game)
                .where(
                    Game.league_id == league_id,
                    Game.game_date == game_date,
                    Game.status == "completed",
                )
                .order_by(Game.started_at, Game.id)
            )
        )

    def _sync_game_boxscore(self, *, league: League, league_key: str, game: Game) -> SyncResult:
        if game.status != "completed":
            logger.info(
                f"skipping boxscore scrape for game league={league_key} source_game_id={game.source_game_id} status={game.status}"
            )
            return SyncResult(skipped=1)
        if self.nba_api_client is None:
            raise ValueError("nba_api client is not configured")

        payload = self.nba_api_client.fetch_boxscore_payload(
            league_key=league_key,
            source_game_id=game.source_game_id,
        )
        parsed_rows = parse_nba_api_boxscore(payload)
        result = self._sync_parsed_boxscore(league=league, game=game, parsed_rows=parsed_rows)
        self.session.commit()
        logger.info(
            f"finished boxscore scrape for game league={league_key} source_game_id={game.source_game_id} "
            f"players_scraped={len(parsed_rows)} created={result.created} updated={result.updated} skipped={result.skipped}"
        )
        return result

    def _sync_parsed_boxscore(self, *, league: League, game: Game, parsed_rows: list[ParsedPlayerBoxscore]) -> SyncResult:
        result = SyncResult()
        teams_by_code = self._get_game_teams_by_code(game=game)

        for parsed_row in parsed_rows:
            if parsed_row.source_game_id != game.source_game_id:
                raise ValueError(
                    f"boxscore row game id mismatch: expected={game.source_game_id} actual={parsed_row.source_game_id}"
                )
            if parsed_row.team_code not in teams_by_code or parsed_row.opponent_team_code not in teams_by_code:
                raise ValueError(
                    "boxscore row contains unknown game team codes: "
                    f"team={parsed_row.team_code} opponent={parsed_row.opponent_team_code}"
                )

            player = self.player_resolution_service.resolve_or_create_player(
                league_id=league.id,
                parsed_player=parsed_row,
            )
            stat = self.session.scalar(
                select(PlayerGameStat).where(
                    PlayerGameStat.player_id == player.id,
                    PlayerGameStat.game_id == game.id,
                )
            )

            if stat is None:
                self.session.add(
                    PlayerGameStat(
                        player_id=player.id,
                        game_id=game.id,
                        team_id=teams_by_code[parsed_row.team_code].id,
                        opponent_team_id=teams_by_code[parsed_row.opponent_team_code].id,
                        started=parsed_row.started,
                        minutes=parsed_row.minutes,
                        points=parsed_row.points,
                        rebounds=parsed_row.rebounds,
                        assists=parsed_row.assists,
                        threes_made=parsed_row.threes_made,
                        steals=parsed_row.steals,
                        blocks=parsed_row.blocks,
                        turnovers=parsed_row.turnovers,
                        offensive_rating=parsed_row.offensive_rating,
                        defensive_rating=parsed_row.defensive_rating,
                        source_row_id=parsed_row.source_row_id,
                    )
                )
                result.created += 1
                continue

            changed = False
            for attr, value in (
                ("team_id", teams_by_code[parsed_row.team_code].id),
                ("opponent_team_id", teams_by_code[parsed_row.opponent_team_code].id),
                ("started", parsed_row.started),
                ("minutes", parsed_row.minutes),
                ("points", parsed_row.points),
                ("rebounds", parsed_row.rebounds),
                ("assists", parsed_row.assists),
                ("threes_made", parsed_row.threes_made),
                ("steals", parsed_row.steals),
                ("blocks", parsed_row.blocks),
                ("turnovers", parsed_row.turnovers),
                ("offensive_rating", parsed_row.offensive_rating),
                ("defensive_rating", parsed_row.defensive_rating),
                ("source_row_id", parsed_row.source_row_id),
            ):
                if getattr(stat, attr) != value:
                    setattr(stat, attr, value)
                    changed = True

            if changed:
                result.updated += 1
            else:
                result.skipped += 1

        return result

    def _get_game_teams_by_code(self, *, game: Game) -> dict[str, Team]:
        teams = list(
            self.session.scalars(
                select(Team).where(
                    Team.id.in_([game.home_team_id, game.away_team_id]),
                )
            )
        )
        if len(teams) != 2:
            raise ValueError(f"could not resolve game teams for game_id={game.id}")
        return {team.abbreviation: team for team in teams}

    def _get_league(self, league_key: str) -> League:
        league = self.session.scalar(select(League).where(League.key == league_key))
        if league is None:
            raise ValueError(f"league not found: {league_key}")
        return league

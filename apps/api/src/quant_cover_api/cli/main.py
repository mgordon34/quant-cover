import argparse
import logging
from datetime import date
from pathlib import Path

from quant_cover_api.db.session import SessionLocal
from quant_cover_api.scraping.clients.nba_api_client import NbaApiClient
from quant_cover_api.scraping.clients.nba_com import NbaComClient
from quant_cover_api.scraping.clients.stathead import StatheadClient
from quant_cover_api.services.boxscore_sync_service import BoxscoreSyncService
from quant_cover_api.services.game_sync_service import GameSyncService
from quant_cover_api.services.sync_result import SyncResult
from quant_cover_api.services.team_sync_service import TeamSyncService

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="quant-cover-cli")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sync_parser = subparsers.add_parser("sync")
    sync_subparsers = sync_parser.add_subparsers(dest="source", required=True)

    stathead_parser = sync_subparsers.add_parser("stathead")
    stathead_subparsers = stathead_parser.add_subparsers(dest="resource", required=True)

    teams_parser = stathead_subparsers.add_parser("teams")
    teams_parser.add_argument("--league", required=True)
    teams_parser.add_argument("--fixture", type=Path)

    nba_com_parser = sync_subparsers.add_parser("nba-com")
    nba_com_subparsers = nba_com_parser.add_subparsers(dest="resource", required=True)

    nba_com_teams_parser = nba_com_subparsers.add_parser("teams")
    nba_com_teams_parser.add_argument("--league", required=True)
    nba_com_teams_parser.add_argument("--fixture", type=Path)

    nba_api_parser = sync_subparsers.add_parser("nba-api")
    nba_api_subparsers = nba_api_parser.add_subparsers(dest="resource", required=True)

    nba_api_games_parser = nba_api_subparsers.add_parser("games")
    nba_api_games_parser.add_argument("--league", required=True)
    date_group = nba_api_games_parser.add_mutually_exclusive_group(required=True)
    date_group.add_argument("--date", type=date.fromisoformat)
    date_group.add_argument("--from-date", dest="from_date", type=date.fromisoformat)
    nba_api_games_parser.add_argument("--to-date", dest="to_date", type=date.fromisoformat)
    nba_api_games_parser.add_argument("--fixture", type=Path)

    nba_api_boxscore_parser = nba_api_subparsers.add_parser("boxscore")
    nba_api_boxscore_parser.add_argument("--league", required=True)
    nba_api_boxscore_parser.add_argument("--game-id", dest="game_id", required=True)
    nba_api_boxscore_parser.add_argument("--fixture", type=Path)

    nba_api_boxscores_parser = nba_api_subparsers.add_parser("boxscores")
    nba_api_boxscores_parser.add_argument("--league", required=True)
    boxscore_date_group = nba_api_boxscores_parser.add_mutually_exclusive_group(required=True)
    boxscore_date_group.add_argument("--date", type=date.fromisoformat)
    boxscore_date_group.add_argument("--from-date", dest="from_date", type=date.fromisoformat)
    nba_api_boxscores_parser.add_argument("--to-date", dest="to_date", type=date.fromisoformat)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "sync" and args.source == "stathead" and args.resource == "teams":
        return run_team_sync(source="stathead", league_key=args.league, fixture_path=args.fixture)

    if args.command == "sync" and args.source == "nba-com" and args.resource == "teams":
        return run_team_sync(source="nba-com", league_key=args.league, fixture_path=args.fixture)

    if args.command == "sync" and args.source == "nba-api" and args.resource == "games":
        return run_game_sync(
            league_key=args.league,
            game_date=args.date,
            from_date=args.from_date,
            to_date=args.to_date,
            fixture_path=args.fixture,
        )

    if args.command == "sync" and args.source == "nba-api" and args.resource == "boxscore":
        return run_boxscore_sync(
            league_key=args.league,
            source_game_id=args.game_id,
            game_date=None,
            from_date=None,
            to_date=None,
            fixture_path=args.fixture,
        )

    if args.command == "sync" and args.source == "nba-api" and args.resource == "boxscores":
        return run_boxscore_sync(
            league_key=args.league,
            source_game_id=None,
            game_date=args.date,
            from_date=args.from_date,
            to_date=args.to_date,
            fixture_path=None,
        )

    parser.error("unsupported command")
    return 2


def run_team_sync(*, source: str, league_key: str, fixture_path: Path | None) -> int:
    session = SessionLocal()

    try:
        service = TeamSyncService(
            session=session,
            stathead_client=StatheadClient(),
            nba_com_client=NbaComClient(),
        )
        if source == "stathead":
            result = service.sync_stathead_teams(league_key=league_key, fixture_path=fixture_path)
        elif source == "nba-com":
            result = service.sync_nba_com_teams(league_key=league_key, fixture_path=fixture_path)
        else:
            raise ValueError(f"unsupported team sync source: {source}")
    except Exception as exc:
        session.rollback()
        print(f"sync failed: {exc}")
        return 1
    finally:
        session.close()

    print(render_sync_result(result))
    return 0


def run_game_sync(
    *,
    league_key: str,
    game_date: date | None,
    from_date: date | None,
    to_date: date | None,
    fixture_path: Path | None,
) -> int:
    session = SessionLocal()

    try:
        logger.info(
            f"starting game scrape session league={league_key} "
            f"date={game_date.isoformat() if game_date is not None else None} "
            f"from_date={from_date.isoformat() if from_date is not None else None} "
            f"to_date={to_date.isoformat() if to_date is not None else None} "
            f"fixture={str(fixture_path) if fixture_path is not None else None}"
        )
        service = GameSyncService(session=session, nba_api_client=NbaApiClient())
        if game_date is not None:
            result = service.sync_nba_api_games_for_date(
                league_key=league_key,
                game_date=game_date,
                fixture_path=fixture_path,
            )
        else:
            if from_date is None or to_date is None:
                raise ValueError("--from-date and --to-date are required together")
            if fixture_path is not None:
                raise ValueError("fixture mode only supports single-date game sync")
            result = service.sync_nba_api_games_for_date_range(
                league_key=league_key,
                start_date=from_date,
                end_date=to_date,
            )
    except Exception as exc:
        session.rollback()
        print(f"sync failed: {exc}")
        return 1
    finally:
        session.close()

    print(render_sync_result(result))
    return 0


def render_sync_result(result: SyncResult) -> str:
    return f"created={result.created} updated={result.updated} skipped={result.skipped}"


def run_boxscore_sync(
    *,
    league_key: str,
    source_game_id: str | None,
    game_date: date | None,
    from_date: date | None,
    to_date: date | None,
    fixture_path: Path | None,
) -> int:
    session = SessionLocal()

    try:
        logger.info(
            f"starting boxscore scrape session league={league_key} "
            f"source_game_id={source_game_id} "
            f"date={game_date.isoformat() if game_date is not None else None} "
            f"from_date={from_date.isoformat() if from_date is not None else None} "
            f"to_date={to_date.isoformat() if to_date is not None else None} "
            f"fixture={str(fixture_path) if fixture_path is not None else None}"
        )
        service = BoxscoreSyncService(session=session, nba_api_client=NbaApiClient())
        if source_game_id is not None:
            result = service.sync_nba_api_boxscore_for_game(
                league_key=league_key,
                source_game_id=source_game_id,
                fixture_path=fixture_path,
            )
        else:
            if game_date is not None:
                result = service.sync_nba_api_boxscores_for_date(
                    league_key=league_key,
                    game_date=game_date,
                )
            else:
                if from_date is None or to_date is None:
                    raise ValueError("--from-date and --to-date are required together")
                result = service.sync_nba_api_boxscores_for_date_range(
                    league_key=league_key,
                    start_date=from_date,
                    end_date=to_date,
                )
        logger.info(
            f"finished boxscore scrape session league={league_key} created={result.created} "
            f"updated={result.updated} skipped={result.skipped}"
        )
    except Exception as exc:
        session.rollback()
        print(f"sync failed: {exc}")
        return 1
    finally:
        session.close()

    print(render_sync_result(result))
    return 0

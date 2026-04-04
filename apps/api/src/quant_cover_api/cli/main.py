import argparse
from pathlib import Path

from quant_cover_api.db.session import SessionLocal
from quant_cover_api.scraping.clients.nba_com import NbaComClient
from quant_cover_api.scraping.clients.stathead import StatheadClient
from quant_cover_api.services.sync_result import SyncResult
from quant_cover_api.services.team_sync_service import TeamSyncService


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

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "sync" and args.source == "stathead" and args.resource == "teams":
        return run_team_sync(source="stathead", league_key=args.league, fixture_path=args.fixture)

    if args.command == "sync" and args.source == "nba-com" and args.resource == "teams":
        return run_team_sync(source="nba-com", league_key=args.league, fixture_path=args.fixture)

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


def render_sync_result(result: SyncResult) -> str:
    return f"created={result.created} updated={result.updated} skipped={result.skipped}"

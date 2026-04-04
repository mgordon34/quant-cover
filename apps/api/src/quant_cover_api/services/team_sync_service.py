from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from quant_cover_api.db.models.league import League
from quant_cover_api.db.models.team import Team
from quant_cover_api.scraping.clients.nba_com import NbaComClient
from quant_cover_api.scraping.clients.stathead import StatheadClient
from quant_cover_api.scraping.parsers.nba_com_teams import parse_nba_com_teams
from quant_cover_api.scraping.parsers.teams import ParsedTeam, parse_stathead_teams
from quant_cover_api.services.sync_result import SyncResult


class TeamSyncService:
    def __init__(
        self,
        *,
        session: Session,
        stathead_client: StatheadClient | None = None,
        nba_com_client: NbaComClient | None = None,
    ) -> None:
        self.session = session
        self.stathead_client = stathead_client
        self.nba_com_client = nba_com_client

    def sync_stathead_teams(self, *, league_key: str, fixture_path: Path | None = None) -> SyncResult:
        league = self._get_league(league_key)
        if self.stathead_client is None:
            raise ValueError("stathead client is not configured")
        html = self.stathead_client.fetch_teams_html(league_key=league_key, fixture_path=fixture_path)
        parsed_teams = parse_stathead_teams(html)

        return self._sync_parsed_teams(league=league, parsed_teams=parsed_teams)

    def sync_nba_com_teams(self, *, league_key: str, fixture_path: Path | None = None) -> SyncResult:
        league = self._get_league(league_key)
        if self.nba_com_client is None:
            raise ValueError("nba.com client is not configured")
        payload = self.nba_com_client.fetch_teams_payload(league_key=league_key, fixture_path=fixture_path)
        for line in payload:
            print(line)
        parsed_teams = parse_nba_com_teams(payload)

        return self._sync_parsed_teams(league=league, parsed_teams=parsed_teams)

    def _sync_parsed_teams(self, *, league: League, parsed_teams: list[ParsedTeam]) -> SyncResult:

        result = SyncResult()
        for parsed_team in parsed_teams:
            team = self.session.scalar(
                select(Team).where(
                    Team.league_id == league.id,
                    Team.abbreviation == parsed_team.abbreviation,
                )
            )
            if team is None:
                self.session.add(
                    Team(
                        league_id=league.id,
                        abbreviation=parsed_team.abbreviation,
                        name=parsed_team.name,
                        is_active=parsed_team.is_active,
                    )
                )
                result.created += 1
                continue

            changed = False
            if team.name != parsed_team.name:
                team.name = parsed_team.name
                changed = True
            if team.is_active != parsed_team.is_active:
                team.is_active = parsed_team.is_active
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

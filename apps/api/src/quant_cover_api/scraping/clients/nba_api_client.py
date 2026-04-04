import json
from datetime import date
from pathlib import Path

from nba_api.stats.endpoints import scoreboardv3


class NbaApiClient:
    def fetch_games_payload(self, *, league_key: str, game_date: date, fixture_path: Path | None = None) -> dict:
        if fixture_path is not None:
            return json.loads(fixture_path.read_text(encoding="utf-8"))

        if league_key != "nba":
            raise ValueError(f"unsupported league for nba_api game sync: {league_key}")

        return scoreboardv3.ScoreboardV3(game_date=game_date.strftime("%m/%d/%Y"), league_id="00").get_dict()

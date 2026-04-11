import json
from pathlib import Path
from urllib import error, request


class NbaComRequestError(RuntimeError):
    pass


class NbaComClient:
    BASE_URL = "https://cdn.nba.com/static/json/liveData"

    def __init__(self) -> None:
        self._headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/123.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json",
        }

    def fetch_teams_payload(self, league_key: str, fixture_path: Path | None = None) -> dict:
        if fixture_path is not None:
            return json.loads(fixture_path.read_text(encoding="utf-8"))

        if league_key != "nba":
            raise ValueError(f"unsupported league for NBA.com team sync: {league_key}")

        req = request.Request(
            f"{self.BASE_URL}/scoreboard/todaysScoreboard_00.json",
            headers=self._headers,
        )
        try:
            with request.urlopen(req, timeout=30.0) as response:
                return json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            raise NbaComRequestError(f"nba.com request failed with status {exc.code}") from exc
        except error.URLError as exc:
            raise NbaComRequestError(f"nba.com request failed: {exc.reason}") from exc

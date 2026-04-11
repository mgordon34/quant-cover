from pathlib import Path
from urllib import error, request


class StatheadRequestError(RuntimeError):
    pass


class StatheadClient:
    BASE_URL = "https://www.basketball-reference.com"

    def __init__(self) -> None:
        self._headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/123.0.0.0 Safari/537.36"
            ),
        }

    def fetch_teams_html(self, league_key: str, fixture_path: Path | None = None) -> str:
        if fixture_path is not None:
            return fixture_path.read_text(encoding="utf-8")

        if league_key != "nba":
            raise ValueError(f"unsupported league for team sync: {league_key}")

        req = request.Request(f"{self.BASE_URL}/teams/", headers=self._headers)
        try:
            with request.urlopen(req, timeout=30.0) as response:
                return response.read().decode("utf-8")
        except error.HTTPError as exc:
            raise StatheadRequestError(f"stathead request failed with status {exc.code}") from exc
        except error.URLError as exc:
            raise StatheadRequestError(f"stathead request failed: {exc.reason}") from exc

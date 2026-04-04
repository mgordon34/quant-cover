from dataclasses import dataclass

from bs4 import BeautifulSoup


@dataclass(frozen=True)
class ParsedTeam:
    abbreviation: str
    name: str
    is_active: bool = True


def parse_stathead_teams(html: str) -> list[ParsedTeam]:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.select_one("table#teams_active")
    if table is None:
        raise ValueError("could not find active teams table")

    teams: list[ParsedTeam] = []
    for row in table.select("tbody tr"):
        link = row.select_one('th[data-stat="franch_name"] a[href*="/teams/"]')
        if link is None:
            continue

        href = link.get("href", "")
        abbreviation = extract_team_code(href)
        team_name = link.get_text(strip=True)
        if not abbreviation or not team_name:
            continue

        teams.append(ParsedTeam(abbreviation=abbreviation, name=team_name))

    if not teams:
        raise ValueError("no teams found in active teams table")

    return teams


def extract_team_code(href: str) -> str:
    parts = [part for part in href.split("/") if part]
    if len(parts) < 2 or parts[0] != "teams":
        return ""
    return parts[1].upper()

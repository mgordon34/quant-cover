# Game And Boxscore Ingestion Plan

## Goal

Define the next ingestion phase after team sync:

- sync games first
- sync boxscores second
- create or update players when they are discovered in boxscores
- persist `player_game_stats` from the same boxscore flow

This plan intentionally avoids building a separate full-league player bootstrap as the next step.

## Core Decision

Use games and boxscores as the primary discovery path for players.

That means:

- `teams` remain a prerequisite dimension table
- `games` become the next canonical fact to ingest
- `players` are upserted when they appear in a game boxscore
- `player_game_stats` are written in the same sync flow

## Why This Approach

### Advantages

- players are discovered in a context that already includes game and team information
- boxscores contain the stat lines that matter most for backtesting
- fewer ingestion paths need to be built up front
- avoids prematurely choosing a separate player-directory endpoint that may be incomplete or unstable
- creates usable historical betting data faster than a dedicated player bootstrap would

### Tradeoff

- players are only discovered once they appear in synced games
- a separate enrichment pass may still be useful later for filling in player metadata

This is acceptable for the current phase because the main goal is to build a reliable data pipeline for games and performance data.

## Data Flow

### Step 1: Team sync

Already implemented.

Purpose:
- establish canonical `teams` rows and team codes needed for later joins

### Step 2: Game sync

Input:
- schedule or scoreboard-style source data

Output:
- `games`

Responsibilities:
- resolve `league`
- resolve `home_team_id` and `away_team_id` by team code
- map source status to the allowed game status values
- upsert games by source-specific identifier when available

### Step 3: Boxscore sync

Input:
- one game identifier at a time

Output:
- upserted `players`
- upserted `player_game_stats`
- optionally updated `games.home_score` and `games.away_score`

Responsibilities:
- fetch boxscore payload for a game
- resolve player identifiers and names
- create missing players
- insert or update stat rows keyed by `(player_id, game_id)`

## Suggested Module Layout

```text
apps/api/src/quant_cover_api/
  scraping/
    clients/
      nba_com.py
    parsers/
      nba_com_games.py
      nba_com_boxscore.py
  services/
    game_sync_service.py
    boxscore_sync_service.py
    player_resolution_service.py
```

## Source Strategy

### Games

Primary source:
- `nba-com`

Reason:
- accessible scoreboard-style JSON has already proven usable in this environment
- games are naturally represented in schedule and scoreboard feeds

### Boxscores

Primary source:
- `nba-com`

Reason:
- once a game source is selected, using the same provider for boxscores reduces cross-source matching complexity

## Phase 1: Game Sync

### Goal

Persist canonical NBA games.

### New modules

- `scraping/parsers/nba_com_games.py`
- `services/game_sync_service.py`

### CLI shape

Suggested command:

```bash
python -m quant_cover_api.cli sync nba-com games --league nba
```

Later extensions:

```bash
python -m quant_cover_api.cli sync nba-com games --league nba --date 2026-04-02
python -m quant_cover_api.cli sync nba-com games --league nba --season 2025-26
```

### Parsed game shape

```python
from dataclasses import dataclass
from datetime import date
from datetime import datetime


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
```

### Sync behavior

- load `League` by key
- fetch source payload
- parse `ParsedGame` rows
- resolve teams by `(league_id, abbreviation)`
- upsert games by `(league_id, stathead_game_id)` or equivalent source game id column strategy
- update scores and status on re-sync

### Game status mapping

The sync layer should map source statuses into the approved DB values:

- `scheduled`
- `in_progress`
- `completed`
- `postponed`
- `cancelled`

Do not store source-specific raw status values directly in `games.status`.

### Acceptance criteria

- game sync inserts valid `games` rows
- re-running sync updates scores/status without duplicates
- unknown team codes fail clearly rather than creating partial rows

## Phase 2: Boxscore Sync

### Goal

Persist players and player stat lines from game boxscores.

### New modules

- `scraping/parsers/nba_com_boxscore.py`
- `services/boxscore_sync_service.py`
- `services/player_resolution_service.py`

### CLI shape

Suggested commands:

```bash
python -m quant_cover_api.cli sync nba-com boxscore --league nba --game-id <source_game_id>
python -m quant_cover_api.cli sync nba-com boxscores --league nba --date 2026-04-02
```

The first implementation should start with a single-game command.

### Parsed boxscore shape

```python
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class ParsedPlayerBoxscore:
    source_game_id: str
    source_player_id: str | None
    full_name: str
    display_name: str
    primary_position: str | None
    team_code: str
    opponent_team_code: str
    started: bool | None
    minutes: Decimal | None
    points: int | None
    rebounds: int | None
    assists: int | None
    threes_made: int | None
    steals: int | None
    blocks: int | None
    turnovers: int | None
    offensive_rating: Decimal | None
    defensive_rating: Decimal | None
    source_row_id: str | None = None
```

## Player Resolution Strategy

### Goal

Create players when they are discovered, but avoid duplicates.

### Resolution order

For each parsed player row:

1. match existing player by `(league_id, stathead_player_id)` or source-specific player id field if present
2. match by exact alias on `(stathead_source, normalized_alias)`
3. match by exact canonical full name within the league
4. create a new player if no match exists

### On create

Store:

- `league_id`
- `full_name`
- `display_name`
- source-specific player id if present
- `primary_position` if present

### On update

Allow safe enrichment of:

- `display_name`
- `primary_position`
- `birth_date` later if a trusted source provides it

Do not add fuzzy matching yet.

## Boxscore Persistence Strategy

### For players

- create missing player rows during boxscore sync
- optionally add `player_aliases` if the source provides alternate names or if a normalized canonical alias should be inserted

### For player stat lines

- resolve the canonical `game`
- resolve the canonical `team` and `opponent_team`
- upsert `player_game_stats` by `(player_id, game_id)`
- update stat columns on re-sync

### For games

Boxscore sync may also update:

- `home_score`
- `away_score`
- `status`

if the boxscore source is more complete than the original game source.

## Suggested Service Boundaries

### `game_sync_service.py`

Responsibilities:

- fetch source game payloads
- parse game rows
- resolve teams
- upsert `games`

Suggested entrypoint:

- `sync_nba_com_games(league_key: str, date: str | None = None) -> SyncResult`

### `player_resolution_service.py`

Responsibilities:

- resolve or create canonical players from boxscore player rows
- centralize player identity logic so it is not duplicated in boxscore sync code

Suggested entrypoint:

- `resolve_player(league_id: int, parsed_player: ParsedPlayerBoxscore) -> Player`

### `boxscore_sync_service.py`

Responsibilities:

- fetch boxscore payload
- parse player rows
- resolve game
- resolve or create players
- upsert `player_game_stats`

Suggested entrypoints:

- `sync_nba_com_boxscore(league_key: str, source_game_id: str) -> SyncResult`
- later `sync_nba_com_boxscores_for_date(league_key: str, date: str) -> SyncResult`

## Recommended Build Order

1. implement `nba_com_games` parser
2. implement `game_sync_service`
3. add CLI command for `sync nba-com games --league nba`
4. verify game sync against fixture or live payload
5. implement `nba_com_boxscore` parser
6. implement `player_resolution_service`
7. implement `boxscore_sync_service`
8. add single-game boxscore CLI command
9. verify players and stat rows are created from boxscore ingestion

## What Not To Build Yet

- no separate full-league player bootstrap command yet
- no fuzzy player matching
- no job queue for boxscore sync yet
- no roster history tables yet
- no public HTTP ingestion routes

## Acceptance Criteria

This effort is complete when:

- games can be synced for NBA through a dedicated command
- a single game boxscore can be synced through a dedicated command
- missing players are created automatically during boxscore sync
- `player_game_stats` rows are inserted or updated idempotently
- re-running the same game/boxscore sync does not create duplicates

## Follow-Up After This

Once game and boxscore sync are stable:

1. add date-range boxscore sync
2. add player enrichment paths if needed
3. add ingestion run tracking if operational visibility is needed
4. only then consider scheduled or queued execution

# Date-Driven Scraping Plan

## Goal

Define the next scraping implementation around a single date-driven workflow:

1. fetch all NBA games for a specific date
2. upsert those games into `games`
3. for each completed game, fetch the boxscore
4. upsert missing players discovered in the boxscore
5. upsert `player_game_stats` for those players

This plan is the concrete next step for scraping after team sync.

## Target User Flow

Given a date such as `2026-04-02`, the system should be able to run one command that:

- loads all games for that date
- inserts or updates the canonical game rows
- identifies which games are completed
- fetches boxscore data for completed games only
- inserts missing players
- inserts or updates player stat rows

## Why This Should Be The Next Step

- it matches the natural workflow of historical sports data collection
- it gives you immediately useful game and player stat data for backtesting
- it avoids overbuilding a separate full-player bootstrap flow
- it keeps player creation tied to actual observed game participation
- it is easy to re-run for a given date idempotently

## Prerequisites

The following must already exist before this workflow runs:

- database migrated
- seed rows for `sports` and `leagues`
- `teams` synced for `nba`

Without `teams`, game and boxscore ingestion will not be able to resolve canonical team foreign keys.

## Source Strategy

Use `nba_api` first for this flow.

Reason:

- it provides dated historical game lookup through NBA stats endpoints
- it is a better fit for historical game and boxscore workflows than the temporary live-feed approach

## Workflow Overview

### Step 1: Sync games for a date

Input:
- league key
- date

Output:
- canonical `games` rows for that date

Command shape:

```bash
python -m quant_cover_api.cli sync nba-api games --league nba --date 2026-04-02
```

Behavior:

- fetch source schedule or scoreboard payload for the date
- parse all games on that date
- resolve `home_team_id` and `away_team_id`
- upsert games by source game id
- update scores and status if the game already exists

### Step 2: Sync completed game boxscores for an inclusive date range

Input:
- league key
- from date
- to date

Output:
- upserted `players`
- upserted `player_game_stats`
- optionally refreshed final scores on `games`

Command shape:

```bash
python -m quant_cover_api.cli sync nba-api boxscores --league nba --from-date 2026-04-02 --to-date 2026-04-07
```

Use the same value for `--from-date` and `--to-date` to sync one day.

Behavior:

- iterate each day from `from_date` to `to_date`, inclusive
- query local `games` for that date and league
- filter to `status = completed`
- fetch a boxscore for each completed game
- parse player rows
- resolve or create players
- upsert player stat rows keyed by `(player_id, game_id)`

### Step 3: Optional combined command

Once Steps 1 and 2 are stable, add a combined orchestration command:

```bash
python -m quant_cover_api.cli sync nba-api day --league nba --date 2026-04-02
```

This command should:

1. sync games for the date
2. sync boxscores for completed games on that date

Do not implement the combined command first. Build the two smaller commands first.

## Suggested Module Layout

```text
apps/api/src/quant_cover_api/
  scraping/
    clients/
      nba_api_client.py
    parsers/
      nba_api_games.py
      nba_api_boxscore.py
  services/
    game_sync_service.py
    boxscore_sync_service.py
    player_resolution_service.py
```

## Parsed Shapes

### Parsed game

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

### Parsed player boxscore row

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

## Service Responsibilities

### `game_sync_service.py`

Responsibilities:

- fetch source game payload for a date
- parse game rows
- resolve teams
- upsert `games`
- return a sync summary

Suggested entrypoint:

- `sync_nba_api_games_for_date(league_key: str, game_date: date) -> SyncResult`

### `player_resolution_service.py`

Responsibilities:

- resolve a parsed player row to a canonical `Player`
- create a new `Player` when no existing match is found
- centralize player identity logic so it is not duplicated inside boxscore sync

Suggested entrypoint:

- `resolve_or_create_player(league_id: int, parsed_player: ParsedPlayerBoxscore) -> Player`

### `boxscore_sync_service.py`

Responsibilities:

- load completed games for a date
- fetch boxscore payload per game
- parse player stat rows
- resolve or create players
- upsert `player_game_stats`
- update game-level scores/status if necessary

Suggested entrypoints:

- `sync_nba_api_boxscores_for_date_range(league_key: str, start_date: date, end_date: date) -> SyncResult`

## Player Resolution Rules

For each player encountered in a boxscore:

1. match by `(league_id, source_player_id)` when present
2. match by exact alias on `(source, normalized_alias)` if alias support is available
3. match by exact `full_name` within the league
4. if no match exists, create a new player row

On create, populate:

- `league_id`
- `full_name`
- `display_name`
- source-specific player id if available
- `primary_position` if available

Do not add fuzzy matching yet.

## Game Status Handling

Only completed games should trigger boxscore sync in the date-driven workflow.

Source statuses must be mapped into the allowed DB values:

- `scheduled`
- `in_progress`
- `completed`
- `postponed`
- `cancelled`

If a source game is not completed, store the game row but skip boxscore ingestion for that game.

## Idempotency Requirements

The date-driven sync must be safe to run repeatedly.

### Games

- upsert by source game id
- update scores/status if they changed
- never create duplicate game rows for the same source game

### Players

- resolve before insert
- only create when no canonical match exists

### Player game stats

- upsert by `(player_id, game_id)`
- update stat fields if the source payload changes
- never create duplicate stat rows for the same player/game pair

## Recommended CLI Sequence

### Phase 1 commands

Build these first:

```bash
python -m quant_cover_api.cli sync nba-api games --league nba --date 2026-04-02
python -m quant_cover_api.cli sync nba-api boxscores --league nba --from-date 2026-04-02 --to-date 2026-04-07
```

### Phase 2 command

Build this only after Phase 1 is stable:

```bash
python -m quant_cover_api.cli sync nba-api day --league nba --date 2026-04-02
```

## Fixtures And Testing Strategy

Each new parser path should support fixture-driven development first.

Recommended fixtures:

- one games payload for a date with multiple games in mixed statuses
- one completed game boxscore payload
- one in-progress or scheduled game payload for negative-path checks

This allows parser and sync verification without depending on the live source every time.

## Recommended Build Order

1. add `nba_com_games.py` parser
2. add `game_sync_service.py`
3. add `sync nba-api games --league nba --date ...` CLI command
4. add fixture for a single date of games
5. verify games are inserted and re-run idempotently
6. add `nba_com_boxscore.py` parser
7. add `player_resolution_service.py`
8. add `boxscore_sync_service.py`
9. add `sync nba-api boxscores --league nba --from-date ... --to-date ...` CLI command
10. verify player creation and player stat upserts for completed games
11. add the combined `day` orchestration command only after the two steps above are stable

## Acceptance Criteria

This effort is complete when:

- games for a specific date can be synced into `games`
- completed games on that date can trigger boxscore sync
- missing players are inserted automatically during boxscore processing
- `player_game_stats` rows are created or updated without duplicates
- re-running the same date sync is idempotent

## What Not To Build Yet

- no worker queue yet
- no public ingestion API routes
- no fuzzy player matching
- no full-league player bootstrap command
- no enrichment-only player sync until boxscore-driven discovery is working

## Recommended Immediate Next Implementation

1. `nba_com_games` parser
2. `game_sync_service`
3. CLI support for `--date`
4. fixture-driven game sync validation
5. then boxscore parser and player-resolution flow

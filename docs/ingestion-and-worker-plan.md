# Ingestion And Worker Plan

## Goal

Define the implementation path for:

- initial Stathead / Sports Reference ingestion
- a CLI-based manual sync workflow
- the later evolution into a job-based worker system

This plan is meant to keep ingestion out of the HTTP API while preserving a clean path toward scheduled jobs and separate worker runtimes.

## Current Position

The repository already has:

- a FastAPI service in `apps/api`
- Postgres-backed core app tables
- NBA data schema foundations for sports, leagues, teams, players, games, and player game stats
- package boundaries for `scraping`, `services`, and `db`

The repository does not yet have:

- ingestion CLI entrypoints
- Stathead clients or parsers
- recurring job orchestration
- a worker runtime

## Core Decision

For now:

- keep ingestion code in the same repo
- keep ingestion code in the same Python package namespace
- do not run ingestion inside HTTP request handlers
- execute ingestion manually through a CLI

Later:

- reuse the same services in a worker runtime
- split worker execution from API execution without splitting the codebase

## Architecture Shape

### Shared code

The same package should hold:

- source clients
- parsers
- normalization logic
- sync services
- DB models

### Separate runtime entrypoints

Use different entrypoints for different execution modes:

- FastAPI app for user-facing API
- CLI for manual sync commands
- future worker entrypoint for queued jobs

The code should be organized so all three entrypoints call the same service layer.

## Target Directory Shape

Short term:

```text
apps/api/src/quant_cover_api/
  cli/
    __init__.py
    main.py
  scraping/
    clients/
      __init__.py
      stathead.py
    parsers/
      __init__.py
      teams.py
      players.py
      games.py
      player_game_stats.py
    jobs/
      __init__.py
  services/
    team_sync_service.py
    player_sync_service.py
    game_sync_service.py
    player_game_stat_sync_service.py
```

Longer term, if runtime separation becomes useful:

```text
apps/
  api/
  worker/
packages/
  python-shared/   # only if a shared package split becomes necessary
```

The recommended near-term choice is to keep everything under `apps/api` until runtime pressure justifies a separate `apps/worker`.

## Responsibility Split

### `scraping/clients`

Responsibilities:

- fetch raw content from Stathead / Sports Reference pages
- handle request headers, retries, timeouts, and session behavior
- return raw HTML or raw text

Should not:

- write to the database
- perform business upserts
- contain product-level orchestration

### `scraping/parsers`

Responsibilities:

- turn raw source documents into structured parsed rows
- normalize obvious source formatting issues
- emit source-shaped parsed objects

Should not:

- open DB sessions
- decide upsert behavior
- coordinate multi-step sync workflows

### `services/*_sync_service.py`

Responsibilities:

- coordinate source fetch + parse + database persistence
- resolve leagues and existing records
- upsert canonical entities
- report created/updated/skipped counts

Should not:

- parse CLI arguments
- expose HTTP concerns

### `cli/main.py`

Responsibilities:

- parse commands and options
- choose the sync service to call
- print human-readable summaries
- return non-zero exit codes on failure

Should not:

- contain scraping logic directly
- contain DB upsert logic directly

## Implementation Phases

### Phase 1: CLI skeleton

Goal:
- create a manual ingestion entrypoint

Deliverables:
- `quant_cover_api.cli.main`
- one command group such as `sync`
- one initial command: `sync stathead teams --league nba`

Suggested invocation:

```bash
uv run python -m quant_cover_api.cli sync stathead teams --league nba
```

or inside the container:

```bash
docker compose -f deploy/docker/docker-compose.yml run --rm api python -m quant_cover_api.cli sync stathead teams --league nba
```

Acceptance criteria:
- command can be invoked cleanly
- command resolves the `nba` league row
- command calls a dedicated team sync service

### Phase 2: Team sync vertical slice

Goal:
- build the first real ingestion path end-to-end

Deliverables:
- `scraping/clients/stathead.py`
- `scraping/parsers/teams.py`
- `services/team_sync_service.py`

Input:
- a Stathead / Sports Reference team listing source for NBA

Parsed output shape:

```python
from dataclasses import dataclass


@dataclass
class ParsedTeam:
    abbreviation: str
    name: str
    is_active: bool = True
```

Sync behavior:
- load `League` by `key`
- fetch source document
- parse team rows
- upsert teams by `(league_id, abbreviation)`
- update mutable fields like `name` and `is_active`
- commit once per command run

Summary output:
- created count
- updated count
- skipped count

Acceptance criteria:
- running the command inserts NBA teams into `teams`
- re-running the command is idempotent

### Phase 3: Player sync

Goal:
- persist canonical players and alias support

Deliverables:
- `scraping/parsers/players.py`
- `services/player_sync_service.py`

Sync behavior:
- upsert players by `(league_id, stathead_player_id)` when available
- otherwise resolve by exact canonical name within league
- populate `player_aliases` when alternate names are available or inferred

Acceptance criteria:
- players can be synced without creating duplicate canonical rows
- aliases are stored deterministically

### Phase 4: Game sync

Goal:
- persist NBA games for a season/date range

Deliverables:
- `scraping/parsers/games.py`
- `services/game_sync_service.py`

Sync behavior:
- resolve home and away teams by abbreviation
- upsert games by `(league_id, stathead_game_id)` when available
- otherwise by `(league_id, game_date, home_team_id, away_team_id)` if required

Acceptance criteria:
- completed and scheduled games can be stored
- game status mapping is aligned with the DB constraint

### Phase 5: Player game stat sync

Goal:
- persist NBA player stat lines

Deliverables:
- `scraping/parsers/player_game_stats.py`
- `services/player_game_stat_sync_service.py`

Sync behavior:
- resolve player, game, team, and opponent team
- upsert by `(player_id, game_id)`
- fill the first-class stat columns from the approved schema

Acceptance criteria:
- repeated sync runs remain idempotent
- player stat rows connect cleanly to games and players

### Phase 6: Worker-ready refactor

Goal:
- make ingestion callable by a worker without changing business logic

Deliverables:
- service interfaces that are runtime-agnostic
- a thin job submission layer later

At this point the CLI should already call services directly. The worker should reuse the same services rather than duplicating ingestion logic.

## Initial CLI Design

Suggested command structure:

```text
quant_cover_api.cli sync stathead teams --league nba
quant_cover_api.cli sync stathead players --league nba
quant_cover_api.cli sync stathead games --league nba --season 2024
quant_cover_api.cli sync stathead player-game-stats --league nba --season 2024
```

This keeps the source and entity explicit without overengineering a command framework.

## First Service Interfaces

Suggested service entrypoints:

- `sync_stathead_teams(league_key: str) -> SyncResult`
- `sync_stathead_players(league_key: str) -> SyncResult`
- `sync_stathead_games(league_key: str, season: str | None = None) -> SyncResult`
- `sync_stathead_player_game_stats(league_key: str, season: str | None = None) -> SyncResult`

Suggested summary type:

```python
from dataclasses import dataclass


@dataclass
class SyncResult:
    created: int = 0
    updated: int = 0
    skipped: int = 0
```

## Source Client Expectations

The first client should handle:

- base URL construction
- timeouts
- basic retries
- stable request headers

It should not yet handle:

- browser automation
- distributed rate limiting
- anti-bot evasion infrastructure

If the source becomes difficult enough that browser automation is required later, that should be added behind the client boundary rather than changing the sync services.

## Name Matching Policy

Initial player resolution order:

1. match by `stathead_player_id`
2. match by exact alias on `(stathead_source, normalized_alias)`
3. match by exact `full_name` within league

Do not implement fuzzy matching in the first phase.

## Worker Evolution Plan

### Stage 1: CLI only

Execution:
- manual developer-triggered commands

Runtime:
- same container image as the API
- different command invocation

### Stage 2: scheduled CLI execution

Execution:
- cron or external scheduler invokes the same CLI commands

Runtime:
- still no internal queue required

### Stage 3: queue-backed worker

Execution:
- API or scheduler enqueues jobs
- worker consumes and calls the same sync services

Possible future structure:
- `apps/worker`
- Redis-backed queue
- separate deployment scaling from API

### Stage 4: operational hardening

Add only when needed:
- ingestion run tracking
- retries
- job timeouts
- structured logs and metrics
- failure notifications

## What Not To Build Yet

- no job queue right now
- no public HTTP ingestion endpoints
- no generalized plugin system
- no multiple-source identity abstraction unless a second source actually lands
- no browser automation until the simple client boundary proves insufficient

## Acceptance Criteria For This Effort

The first milestone is complete when:

- a CLI entrypoint exists
- `sync stathead teams --league nba` runs from the codebase
- the command inserts or updates `teams`
- the command is idempotent
- the sync path is implemented through client -> parser -> service -> DB
- no HTTP route is required for ingestion

## Recommended Build Order

1. add `cli/main.py`
2. add a small CLI command parser
3. add `SyncResult`
4. add `scraping/clients/stathead.py`
5. add `scraping/parsers/teams.py`
6. add `services/team_sync_service.py`
7. add one root-level make target for running the CLI in the container
8. validate that NBA teams can be synced repeatedly without duplicates

## Suggested Follow-Up After Team Sync

1. player sync
2. game sync
3. player game stat sync
4. ingestion run tracking if needed
5. worker runtime only after manual and scheduled ingestion have proven useful

# Quant Cover

Quant Cover is a clean restart of a sports betting research platform built around quantitative strategy development, backtesting, and data-driven analysis.

The initial product focus is the NBA. Over time, the platform is intended to support:

- user accounts and paid access
- configurable betting strategies
- reproducible backtest sessions
- historical and live market data ingestion
- data collection from public sports-reference style sources and sportsbook feeds

## Current Status

This repository is at the start of a rebuild. The near-term goal is to establish a clean backend-first foundation before adding the frontend and product features.

The first implementation targets:

- Python backend managed with `uv`
- FastAPI for the HTTP API
- Postgres as the primary database
- Docker Compose for local development
- a code layout that is ready for scraping, strategy execution, and future background jobs

The current scaffold plan is tracked in `plan.md`.

The initial scaffold now includes:

- `apps/api` for the Python FastAPI service
- `deploy/docker/docker-compose.yml` for local development
- a minimal app entrypoint with `GET /health`
- SQLAlchemy and Alembic setup for the first core tables

## Architectural Direction

The intended shape of the project is a monorepo with a backend-first workflow.

Planned top-level structure:

```text
apps/
  api/        Python API service
deploy/
  docker/     Local development environment
```

Expected backend package boundaries:

- `api`: HTTP routes and request/response models
- `domain`: core business concepts and rules
- `services`: orchestration and use-case logic
- `scraping`: source clients, parsers, and ingest jobs
- `db`: persistence and database integration

This repository should avoid collapsing into a single process where API handlers, scraping, persistence, and strategy logic are tightly coupled.

## Product Direction

The long-term product should be designed around a stable API for:

- users
- strategies
- strategy versions
- backtest sessions
- backtest runs
- market and player data

Even before billing is implemented, the system should stay compatible with a future paid multi-user product.

## Development Principles

- Start small, but keep boundaries clean.
- Prefer simple modules over early infrastructure.
- Keep scraping logic isolated from HTTP handlers.
- Design persistence and API contracts so workers can be added later without rewrites.
- Favor readability and maintainability over clever abstractions.

## For Agents And New Contributors

Start each session by reading:

1. `README.md`
2. `AGENTS.md`
3. `plan.md`

Before making changes:

- inspect the current repository structure
- confirm the work matches the direction in `plan.md`
- prefer extending existing structure over inventing parallel patterns
- keep edits minimal and aligned with the current phase of the project

Current repository expectations:

- the repo is early-stage and intentionally sparse
- avoid overbuilding features that are not yet needed
- backend structure and local development setup take priority over feature work
- comments should be rare and only used when code intent is otherwise hard to see

## Near-Term Roadmap

1. Scaffold the Python API app with `uv`
2. Add Docker Compose with Postgres
3. Expose a minimal FastAPI health endpoint
4. Add database wiring and migrations
5. Add initial core entities for users, strategies, and backtest runs
6. Introduce scraping entrypoints behind clean package boundaries

## Non-Goals Right Now

- full worker infrastructure
- production billing flows
- advanced scraping bypass logic
- frontend implementation
- full strategy engine

## Local Development

This repository uses `direnv` for local environment variables.

Before starting the stack:

```bash
direnv allow
```

Start the local environment:

```bash
direnv exec . docker compose -f deploy/docker/docker-compose.yml up --build
```

From the repository root, you can also use:

```bash
make up
```

Other useful commands:

```bash
make down
make build
make logs
make ps
make test
make test-unit
make test-integration
make lint
make format
make check
make install-hooks
make migrate
make sync-nba-teams
make sync-nba-teams-fixture
make sync-nba-com-teams
make sync-nba-com-teams-fixture
make sync-nba-api-games DATE=YYYY-MM-DD
make sync-nba-api-games-fixture
make sync-nba-api-games-range FROM=YYYY-MM-DD TO=YYYY-MM-DD
```

The root `Makefile` runs Compose through `direnv`, so the values from `.envrc` are loaded automatically.

For local Python tooling outside Docker, install the app and dev dependencies with `uv sync --project apps/api --group dev`.

To enable the repo hooks:

```bash
make install-hooks
```

The pre-commit config runs `ruff check --fix` and `ruff format` against `apps/api`.

Once the app is running:

- API root: `http://localhost:8000/`
- health endpoint: `http://localhost:8000/health`
- strategies endpoint: `http://localhost:8000/strategies`

Expected health response:

```json
{
  "status": "ok",
  "service": "quant-cover-api"
}
```

Apply the initial database migration after the containers are up:

```bash
make migrate
```

The schema migrations also seed the initial `sports` and `leagues` rows for `basketball` and `nba`.

The first ingestion CLI is available for syncing NBA teams from Stathead / Sports Reference.

Live source sync:

```bash
make sync-nba-teams
```

Fixture-based sync for local verification:

```bash
make sync-nba-teams-fixture
```

An NBA.com source path is also available for teams.

Live NBA.com sync:

```bash
make sync-nba-com-teams
```

Fixture-based NBA.com sync:

```bash
make sync-nba-com-teams-fixture
```

Date-based NBA game sync now uses `nba_api`.

Live historical/current-date game sync:

```bash
make sync-nba-api-games DATE=2026-04-02
```

Historical date-range sync with a built-in 1 second delay between per-date requests:

```bash
make sync-nba-api-games-range FROM=2026-04-01 TO=2026-04-07
```

Fixture-based date sync:

```bash
make sync-nba-api-games-fixture
```

Fixture mode currently supports single-date game sync only.

The first API slice currently supports listing and creating strategies.

Create a user:

```bash
curl -X POST "http://localhost:8000/users" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "matt@example.com",
    "display_name": "Matt"
  }'
```

Fetch a user:

```bash
curl "http://localhost:8000/users/1"
```

List strategies for a user:

```bash
curl "http://localhost:8000/strategies?user_id=1"
```

Create a strategy for a user:

```bash
curl -X POST "http://localhost:8000/strategies" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "name": "Simple pace filter",
    "description": "Initial test strategy",
    "configuration": {"min_edge": 0.03}
  }'
```

For now, strategies require an existing `users.id`. Auth is not implemented yet.

Create a backtest run:

```bash
curl -X POST "http://localhost:8000/backtest-runs" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "strategy_id": 1,
    "dataset_version": "nba-2024-regular-season-v1",
    "parameters": {
      "start_date": "2024-10-22",
      "end_date": "2025-04-13"
    }
  }'
```

List backtest runs for a user:

```bash
curl "http://localhost:8000/backtest-runs?user_id=1"
```

Fetch a backtest run:

```bash
curl "http://localhost:8000/backtest-runs/1"
```

## Notes

- The old repository that informed this restart lives at `../kornet-kover`.
- This repository should stay focused on a clean, maintainable rebuild rather than incremental carry-over of old architectural mistakes.
- The default local environment values are stored in `.envrc`.

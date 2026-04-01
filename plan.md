# Initial Scaffold Plan

## Goal

Set up the initial backend-first project structure for Quant Cover using Python with `uv`, FastAPI, Docker Compose, and Postgres. Keep the implementation intentionally minimal so the repo starts clean, runs locally, and is ready for future expansion into scraping, APIs, and backtesting.

## Scope

This first step will only:

- create the repo structure
- scaffold the Python backend package
- add Docker Compose for local development
- add a Postgres service
- expose a minimal FastAPI app with `GET /health`
- create empty module boundaries for scraping and future domain logic

This first step will not yet include:

- real scraping logic
- worker infrastructure
- database models or migrations
- billing
- frontend
- authentication
- strategy or backtest features

## Proposed Repository Structure

```text
quant-cover/
  apps/
    api/
      pyproject.toml
      Dockerfile
      src/
        quant_cover_api/
          __init__.py
          main.py
          config.py
          api/
            __init__.py
            health.py
          domain/
            __init__.py
          services/
            __init__.py
          scraping/
            __init__.py
            clients/
              __init__.py
            parsers/
              __init__.py
            jobs/
              __init__.py
          db/
            __init__.py
      tests/
        __init__.py
  deploy/
    docker/
      docker-compose.yml
  .envrc
  .gitignore
  README.md
```

## Architecture Intent

### Backend

The backend starts as a single FastAPI app, but its internal layout should already reflect the future architecture:

- `api/`: HTTP routes and request/response handling
- `domain/`: core business concepts
- `services/`: business workflows and orchestration
- `scraping/`: future ingestion logic, isolated from the API layer
- `db/`: future database wiring and persistence layer

This keeps the first implementation simple while avoiding a rewrite later.

### Scraping

Scraping should not be implemented yet, but the package boundaries should exist from day one:

- `scraping/clients`: raw fetchers for source sites/APIs
- `scraping/parsers`: parsing and extraction logic
- `scraping/jobs`: orchestration entrypoints for sync jobs

This makes it easy to add background execution later without mixing scraping logic into API handlers.

### Docker Compose

Local development should include:

- `api` service for the Python backend
- `postgres` service for the database

Even though the app will not use the database yet, bringing Postgres in early helps establish the local development environment and future connection conventions.

## Dependencies

### Add now

- `fastapi`
- `uvicorn`
- `pydantic-settings`

### Defer until phase 2

- `sqlalchemy`
- `alembic`
- `psycopg`
- `httpx`
- scraping libraries
- worker/queue libraries

## API Requirements

For this first scaffold, the backend only needs:

- a FastAPI app
- `GET /health`

Expected response:

```json
{
  "status": "ok",
  "service": "quant-cover-api"
}
```

Optionally, the app can also log a simple startup message like `hello world`.

## Docker Requirements

### `api` service

- build from `apps/api/Dockerfile`
- mount source code for local development
- expose the app on port `8000`
- read environment variables from the project root

### `postgres` service

- use the official Postgres image
- expose port `5432`
- configure a database, user, and password
- use a named volume for persistence

## Configuration

Create a root `.envrc` with values like:

- `APP_ENV`
- `APP_HOST`
- `APP_PORT`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `DATABASE_URL`

The Python app should load config from a centralized `config.py`.

## README Requirements

The initial `README.md` should include:

- what the project is
- current stack
- repository structure
- how to start the local environment
- where the API runs
- how to verify `GET /health`
- what is intentionally not built yet

## Acceptance Criteria

The scaffold is complete when:

- the repo structure exists
- the Python app starts successfully
- Docker Compose starts both `api` and `postgres`
- the API is reachable locally
- `GET /health` returns a successful response
- the structure is ready for future scraping and database work

## Implementation Order

1. create root files: `.gitignore`, `.envrc`, `README.md`
2. create `apps/api` project with `uv`
3. add `pyproject.toml`
4. create `src/quant_cover_api` package structure
5. add `config.py`
6. add FastAPI app entrypoint in `main.py`
7. add health route
8. create `Dockerfile` for the API
9. create `deploy/docker/docker-compose.yml`
10. verify local startup with Docker Compose

## Immediate Next Phase After This

Once this scaffold is working, the next logical step is:

- add SQLAlchemy
- add Alembic
- create first database wiring
- add initial core tables such as:
  - `users`
  - `strategies`
  - `backtest_runs`

## Notes

- Start without workers
- Keep the code worker-ready by separating services from routes
- Keep scraping isolated from API code
- Use a monorepo for now
- Add the frontend later once the backend and data model are grounded

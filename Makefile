COMPOSE_FILE := deploy/docker/docker-compose.yml
COMPOSE := direnv exec . docker compose -f $(COMPOSE_FILE)
API_UV := uv run --project apps/api

.PHONY: up down build logs ps restart migrate test test-unit test-integration lint format check pre-commit install-hooks sync-nba-teams sync-nba-teams-fixture sync-nba-com-teams sync-nba-com-teams-fixture sync-nba-api-games sync-nba-api-games-fixture sync-nba-api-games-range sync-nba-api-boxscore sync-nba-api-boxscores sync-nba-api-boxscores-range

up:
	$(COMPOSE) up --build

down:
	$(COMPOSE) down

build:
	$(COMPOSE) build

logs:
	$(COMPOSE) logs -f

ps:
	$(COMPOSE) ps

restart:
	$(COMPOSE) down
	$(COMPOSE) up --build

migrate:
	$(COMPOSE) run --rm api alembic upgrade head

test:
	$(API_UV) pytest

test-unit:
	$(API_UV) pytest apps/api/tests/unit

test-integration:
	$(API_UV) pytest apps/api/tests/integration

lint:
	$(API_UV) ruff check apps/api

format:
	$(API_UV) ruff check --fix apps/api
	$(API_UV) ruff format apps/api

check:
	$(API_UV) ruff check apps/api
	$(API_UV) ruff format --check apps/api
	$(API_UV) pytest

pre-commit:
	$(API_UV) pre-commit run --all-files

install-hooks:
	$(API_UV) pre-commit install

sync-nba-teams:
	$(COMPOSE) run --build --rm api python -m quant_cover_api.cli sync stathead teams --league nba

sync-nba-teams-fixture:
	$(COMPOSE) run --build --rm api python -m quant_cover_api.cli sync stathead teams --league nba --fixture /app/src/quant_cover_api/scraping/fixtures/stathead_nba_teams.html

sync-nba-com-teams:
	$(COMPOSE) run --build --rm api python -m quant_cover_api.cli sync nba-com teams --league nba

sync-nba-com-teams-fixture:
	$(COMPOSE) run --build --rm api python -m quant_cover_api.cli sync nba-com teams --league nba --fixture /app/src/quant_cover_api/scraping/fixtures/nba_com_nba_teams.json

sync-nba-api-games:
	$(COMPOSE) run --build --rm api python -m quant_cover_api.cli sync nba-api games --league nba --date $(DATE)

sync-nba-api-games-range:
	$(COMPOSE) run --build --rm api python -m quant_cover_api.cli sync nba-api games --league nba --from-date $(FROM) --to-date $(TO)

sync-nba-api-games-fixture:
	$(COMPOSE) run --build --rm api python -m quant_cover_api.cli sync nba-api games --league nba --date 2026-04-02 --fixture /app/src/quant_cover_api/scraping/fixtures/nba_api_games_2026-04-02.json

sync-nba-api-boxscore:
	$(COMPOSE) run --build --rm api python -m quant_cover_api.cli sync nba-api boxscore --league nba --game-id $(GAME_ID)

sync-nba-api-boxscores:
	$(COMPOSE) run --build --rm api python -m quant_cover_api.cli sync nba-api boxscores --league nba --date $(DATE)

sync-nba-api-boxscores-range:
	$(COMPOSE) run --build --rm api python -m quant_cover_api.cli sync nba-api boxscores --league nba --from-date $(FROM) --to-date $(TO)

COMPOSE_FILE := deploy/docker/docker-compose.yml
COMPOSE := direnv exec . docker compose -f $(COMPOSE_FILE)

.PHONY: up down build logs ps restart

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

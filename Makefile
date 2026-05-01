COMPOSE = docker compose
CLAWVIS = ./clawvis

.PHONY: down up update init clawvis-start clawvis-doctor clawvis-shutdown clawvis-restart clawvis-update-status clawvis-update-stable

down:
	$(COMPOSE) down -v

up:
	$(COMPOSE) up -d --build

update:
	$(COMPOSE) pull
	$(COMPOSE) build --pull
	$(COMPOSE) up -d

init:
	curl -fsSL https://raw.githubusercontent.com/ldom1/clawvis/main/get.sh | bash

clawvis-start:
	$(CLAWVIS) start

clawvis-doctor:
	$(CLAWVIS) doctor

clawvis-shutdown:
	$(CLAWVIS) shutdown

clawvis-restart:
	$(CLAWVIS) restart

clawvis-update-status:
	$(CLAWVIS) update status

clawvis-update-stable:
	$(CLAWVIS) update --channel stable

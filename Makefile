.PHONY: help install run test lint clean docker-build docker-up docker-down dev-up dev-down hml-up hml-down all-up all-down sync-db-from-prd etl-municipios etl-tse etl-comparecimento etl db-shell migrate migration

help:
	@echo "Comandos disponíveis no ecossistema datapoliRS:"
	@echo "  make all-up          - Sobe simultaneamente os ambientes DEV (3000/8000) e HML (8080/8081) com banco compartilhado"
	@echo "  make all-down        - Derruba os ambientes DEV e HML"
	@echo "  make dev-up          - Sobe o ambiente de DESENVOLVIMENTO local (Portas 3000 / 8000)"
	@echo "  make dev-down        - Derruba o ambiente de desenvolvimento"
	@echo "  make hml-up          - Sobe o ambiente de HOMOLOGAÇÃO local (Portas 8080 / 8081)"
	@echo "  make hml-down        - Derruba o ambiente de homologação"
	@echo "  make sync-db-from-prd - Sincroniza o banco local extraindo dump de PRD com sanitização LGPD (Zero-Leakage)"
	@echo "  make docker-up       - Alias para make dev-up"
	@echo "  make docker-down     - Alias para make dev-down"
	@echo "  make migrate         - Aplica as migrations pendentes (alembic upgrade head)"
	@echo "  make db-shell        - Conecta diretamente ao PostgreSQL não-produtivo via psql no container"
	@echo "  make run             - Executa a API localmente na porta 8000"
	@echo "  make test            - Executa a suíte de testes com pytest"
	@echo "  make clean           - Remove caches do Python e testes"

install:
	pip install -r backend/requirements.txt

# --- Ambientes DEV e HML Simultâneos (ADR 044 / ADR 047) ---
dev-up:
	docker compose -f docker-compose.yml up -d

dev-down:
	docker compose -f docker-compose.yml down

hml-up:
	docker compose -f docker-compose.hml.yml up -d

hml-down:
	docker compose -f docker-compose.hml.yml down

all-up:
	docker compose -f docker-compose.yml up -d
	docker compose -f docker-compose.hml.yml up -d

all-down:
	docker compose -f docker-compose.hml.yml down || true
	docker compose -f docker-compose.yml down || true

docker-up: dev-up
docker-down: dev-down
docker-build:
	docker compose -f docker-compose.yml build

# --- Sincronização Segura de Banco (Regra 18 / ADR 044) ---
sync-db-from-prd:
	./scripts/sync_db_non_prod.sh

# --- Pipelines ETL e Banco de Dados ---
etl-municipios:
	python -m etl.import_municipios_geojson

etl-tse:
	python -m etl.ingest_tse --ano $(ano)

etl-comparecimento:
	python -m etl.ingest_comparecimento --ano $(ano)

etl: etl-municipios etl-tse etl-comparecimento

db-shell:
	docker exec -it datapoli_postgres_non_prod psql -U datapoli_user -d datapoli_db

migrate:
	cd backend && alembic upgrade head

migration:
	cd backend && alembic revision -m "$(msg)"

run:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	cd backend && pytest -v --asyncio-mode=auto

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +

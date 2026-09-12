.PHONY: help install run test lint clean docker-build docker-up docker-down etl-municipios etl-tse etl-comparecimento etl db-shell migrate migration

help:
	@echo "Comandos disponíveis no ecossistema datapoliRS:"
	@echo "  make install         - Instala dependências no ambiente virtual"
	@echo "  make docker-up       - Sobe os serviços (PostgreSQL PostGIS, Redis, API) via Docker Compose"
	@echo "  make docker-down     - Para todos os containers Docker"
	@echo "  make migrate         - Aplica as migrations pendentes (alembic upgrade head)"
	@echo "  make migration msg='descrição' - Gera uma nova migration vazia"
	@echo "  make etl-municipios  - Executa a carga geoespacial de municípios no PostGIS"
	@echo "  make etl-tse ano=2022 - Executa o pipeline de ingestão do TSE com DuckDB para o ano informado"
	@echo "  make etl-comparecimento ano=2022 - Executa a carga de eleitorado apto/comparecimento/abstenções para o ano informado"
	@echo "  make etl ano=2022    - Executa todos os pipelines ETL de carga (municípios + TSE + comparecimento do ano informado)"
	@echo "  make db-shell        - Conecta diretamente ao PostgreSQL via psql no container"
	@echo "  make run             - Executa a API localmente na porta 8000"
	@echo "  make test            - Executa a suíte de testes com pytest"
	@echo "  make clean           - Remove caches do Python e testes"

install:
	pip install -r backend/requirements.txt

docker-build:
	docker compose build

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

etl-municipios:
	python -m etl.import_municipios_geojson

etl-tse:
	python -m etl.ingest_tse --ano $(ano)

etl-comparecimento:
	python -m etl.ingest_comparecimento --ano $(ano)

etl: etl-municipios etl-tse etl-comparecimento

db-shell:
	docker exec -it datapoli_postgres psql -U datapoli_user -d datapoli_db

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

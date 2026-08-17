.PHONY: help install run test lint clean docker-build docker-up docker-down

help:
	@echo "Comandos disponíveis:"
	@echo "  make install      - Instala dependências do projeto"
	@echo "  make run          - Executa a API localmente na porta 8000"
	@echo "  make test         - Executa a suíte de testes com pytest"
	@echo "  make docker-build - Constrói a imagem Docker"
	@echo "  make docker-up    - Inicia o container via docker-compose"
	@echo "  make docker-down  - Para os containers Docker"
	@echo "  make clean        - Remove caches do Python e testes"

install:
	pip install -r requirements.txt

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest -v --asyncio-mode=auto

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +

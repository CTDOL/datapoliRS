# Worker de cargas do ETL eleitoral (python -m etl.worker).
# Contexto de build: raiz do repositório.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY etl ./etl

# ZIPs do TSE ficam num volume nomeado (ver docker-compose.prod.yml), não na imagem.
VOLUME ["/app/etl/data"]

CMD ["python", "-m", "etl.worker"]

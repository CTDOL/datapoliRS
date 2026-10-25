FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Usuário sem privilégio para a API. O diretório de uploads precisa ser
# gravável por ele: o main.py cria app/uploads/liderancas na inicialização.
# O diretório nasce aqui porque um volume nomeado novo herda o dono do caminho
# da imagem. Sem ele, o volume sai como root e a API não sobe (2026-10-24).
RUN mkdir -p app/uploads/liderancas \
    && useradd --system --uid 1000 --no-create-home app \
    && chown -R app:app /app
USER app

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

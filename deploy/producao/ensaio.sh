#!/usr/bin/env bash
# Ensaio do deploy de produção com volumes novos (job ensaio-deploy de deploy-producao.yml).
#
# Monta o compose de produção com imagens construídas deste checkout e roda os mesmos scripts da
# esteira (pull_up, health, carga e o seed). Não toca a VPS nem o GHCR.
# Cobre: wipe com volumes novos, permissão do volume de uploads, migrações do zero, seed, /health da
# API e conexão do ETL com o Redis. Não cobre: frontend, geoipupdate e arm64 (ver ensaio_compose.py).
# Uso: bash deploy/producao/ensaio.sh   (exige Docker com compose v2, rsync, openssl e python3)
set -euo pipefail

RAIZ="$(cd "$(dirname "$0")/../.." && pwd)"
PYTHON="${PYTHON:-python3}"
ID="ensaio$(date +%s)"
IMAGEM_API="ghcr.io/ctdol/datapolirs-api:$ID"
IMAGEM_ETL="ghcr.io/ctdol/datapolirs-etl:$ID"
DIR="$(mktemp -d)"
CONTEXTO="$(mktemp -d)"
export COMPOSE_PROJECT_NAME="$ID" RELEASE_TAG="$ID" SNAPSHOT_DIR="$DIR"

limpar() {
  (cd "$DIR" && docker compose -f docker-compose.prod.yml --env-file .env.prod down -v --remove-orphans > /dev/null 2>&1) || true
  docker image rm -f "$IMAGEM_API" "$IMAGEM_ETL" > /dev/null 2>&1 || true
  rm -rf "$DIR" "$CONTEXTO"
}
trap limpar EXIT

compose() {
  (cd "$DIR" && docker compose -f docker-compose.prod.yml --env-file .env.prod "$@")
}

falha() {
  echo "FALHA no ensaio: $1" >&2
  exit 1
}

# Cada script de produção termina com um eco de marca. Sem a marca, o script parou no meio
# sem erro: é exatamente o que o stdin mal fechado causava no deploy.
conferir_marca() {
  grep -qx "$1" "$2" || falha "a etapa não chegou ao fim (sem $1). O script parou antes do último eco."
}

echo "== Ensaio $ID: contexto limpo, sem backend/app/uploads (como o checkout do CI)"
rsync -a --exclude 'frontend/' --exclude '.git/' --exclude '.venv/' --exclude 'node_modules/' \
  --exclude '__pycache__/' --exclude 'backend/app/uploads/' "$RAIZ/" "$CONTEXTO/repo/"

echo "== Construindo as imagens api e etl"
docker build -q -t "$IMAGEM_API" "$CONTEXTO/repo/backend" > /dev/null
docker build -q -t "$IMAGEM_ETL" -f "$CONTEXTO/repo/etl/Dockerfile" "$CONTEXTO/repo" > /dev/null

echo "== Compose do ensaio: produção sem geoipupdate e frontend, segredos aleatórios por execução"
cat > "$DIR/.env.prod" <<EOF
ENVIRONMENT=production
POSTGRES_USER=ensaio
POSTGRES_PASSWORD=$(openssl rand -hex 16)
POSTGRES_DB=ensaio
SECRET_KEY=$(openssl rand -hex 32)
ADMIN_PASSWORD=$(openssl rand -hex 16)
ADMIN_EMAIL=ensaio@invalid.local
APP_DOMAIN=ensaio.invalid
APP_PROTOCOL=https
EOF
cp "$RAIZ/docker-compose.prod.yml" "$DIR/docker-compose.prod.original.yml"
(cd "$DIR" && docker compose -f docker-compose.prod.original.yml --env-file .env.prod config --format json) \
  | "$PYTHON" "$RAIZ/deploy/producao/ensaio_compose.py" > "$DIR/docker-compose.prod.yml"

echo "== 1/4 Pull + up com wipe (volumes novos)"
cat "$RAIZ/deploy/producao/pull_up.sh" | bash -s -- "$DIR" "$ID" true 2>&1 | tee "$DIR/pull_up.log"
conferir_marca PULL_UP_OK "$DIR/pull_up.log"

echo "== 2/4 Health check da API e dos serviços"
cat "$RAIZ/deploy/producao/health.sh" | bash -s -- "$DIR" "$ID" 2>&1 | tee "$DIR/health.log"
conferir_marca HEALTH_OK "$DIR/health.log"

echo "== 3/4 Carga votacao 2026 (municípios e fila)"
# Avisos do ETL saem pelo stderr: por isso a captura inclui 2>&1, senão a asserção do Redis não os vê.
cat "$RAIZ/deploy/producao/carga.sh" | bash -s -- "$DIR" "$ID" votacao 2026 2>&1 | tee "$DIR/carga.log"
conferir_marca CARGA_OK "$DIR/carga.log"
if grep -q "invalidar o cache Redis" "$DIR/carga.log"; then
  falha "o ETL não alcançou o Redis (REDIS_URL do etl-worker)."
fi

echo "== 4/4 Seed do super-admin, com senha de ensaio"
printf '%s\n' "$(openssl rand -hex 12)" | compose exec -T api python -m scripts.seed_plataforma --producao 2>&1 | tee "$DIR/seed.log"
grep -q "^Super-admin:" "$DIR/seed.log" || falha "o seed não confirmou o super-admin."

echo "== Conferências no banco"
banco() {
  compose exec -T postgres psql -U ensaio -d ensaio -tAc "$1" < /dev/null | tr -d '[:space:]'
}
saida_alembic="$(compose run --rm --no-deps api alembic current < /dev/null 2>/dev/null)"
grep -q "(head)" <<< "$saida_alembic" || falha "o schema não está no head do alembic."
super_admins="$(banco "select count(*) from tb_users where role = 'super_admin'")"
[ "$super_admins" = "1" ] || falha "esperado 1 super-admin, achou $super_admins."
municipios="$(banco "select count(*) from tb_municipios")"
[ "$municipios" -ge 496 ] || falha "esperado ao menos 496 municípios, achou $municipios."
echo "ENSAIO OK: schema no head, super-admin=$super_admins, municípios=$municipios"

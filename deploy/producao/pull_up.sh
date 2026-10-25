#!/usr/bin/env bash
# Snapshot, wipe opcional, migrações e up da esteira de produção (ver .github/workflows/deploy-producao.yml).
# Uso: pull_up.sh <pasta_da_vps> <release_tag> <wipe: true|false>
#
# Roda no servidor com o script chegando pelo stdin (ssh bash -s). Por isso cada comando que lê
# stdin recebe "< /dev/null": sem isso o docker consome o resto do script, que termina sem erro.
# Foi o que deixou o wipe e as migrações sem rodar no deploy da v0.2.0 (2026-10-24).
# O último eco é a prova de conclusão: o runner só aceita o deploy se ele aparecer.
set -e
cd "$1"
export RELEASE_TAG="$2"
WIPE="$3"
COMPOSE="docker compose -f docker-compose.prod.yml --env-file .env.prod"

# Em volume novo, o entrypoint do Postgres sobe um servidor temporário que aceita só o socket Unix.
# Um pg_isready sem -h responde OK nessa fase, e o alembic ainda toma "connection refused" no TCP.
# Por isso a checagem é por TCP (127.0.0.1), que só abre depois do servidor definitivo.
esperar_postgres() {
  for _ in $(seq 1 30); do
    $COMPOSE exec -T postgres sh -c 'pg_isready -h 127.0.0.1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < /dev/null > /dev/null 2>&1 && return 0
    sleep 2
  done
  echo "Postgres não subiu a tempo." >&2
  exit 1
}

# Migrações antes da troca da API: o banco sobe sem recriar a API atual, e o alembic roda
# num container descartável. Se a migração falhar, o set -e aborta e a API anterior segue no ar.
$COMPOSE up -d postgres redis
esperar_postgres

# Snapshot antes da migração: lastro de restauração, sem apagar nada.
SNAPSHOT="${SNAPSHOT_DIR:-$HOME}/pre_${RELEASE_TAG}_$(date +%Y%m%d%H%M%S).dump"
$COMPOSE exec -T postgres sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' < /dev/null > "$SNAPSHOT"
test -s "$SNAPSHOT" || { echo "Snapshot pré-migração vazio: abortando." >&2; exit 1; }
echo "Snapshot pré-migração: $SNAPSHOT"

# Wipe (só com wipe_banco=true, já validado no runner): derruba os containers e apaga os volumes do
# projeto. O banco e os uploads antigos saem do ar. O snapshot acima fica em $HOME para restauração.
if [ "$WIPE" = "true" ]; then
  echo "WIPE: removendo containers e volumes do projeto. Snapshot preservado em $SNAPSHOT."
  $COMPOSE down -v --remove-orphans
  $COMPOSE up -d postgres redis
  esperar_postgres
  echo "Postgres limpo e pronto para as migrações."
fi

$COMPOSE run --rm --no-deps api alembic upgrade head < /dev/null
$COMPOSE up -d
echo "PULL_UP_OK"

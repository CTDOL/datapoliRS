#!/usr/bin/env bash
# Carga inicial da esteira de produção. Uso: carga.sh <pasta_da_vps> <release_tag> <tipo> <ano>
#
# Municípios primeiro; depois a carga entra na fila e o worker a executa em seguida.
# Ambos são idempotentes no que toca o banco. Ver o comentário de pull_up.sh sobre o "< /dev/null".
set -e
cd "$1"
export RELEASE_TAG="$2"
COMPOSE="docker compose -f docker-compose.prod.yml --env-file .env.prod"

$COMPOSE run --rm --no-deps etl-worker python -m etl.import_municipios_geojson < /dev/null
$COMPOSE run --rm --no-deps etl-worker python -m etl.enfileirar_carga "$3" "$4" < /dev/null
echo "CARGA_OK"

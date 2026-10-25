#!/usr/bin/env bash
# Health check da esteira de produção. Uso: health.sh <pasta_da_vps> <release_tag>
#
# Confere o /health da API por dentro do container (a porta não é publicada no host) e se todos os
# serviços do compose estão rodando. Um crash loop da API reprova aqui: o status "running" sozinho
# aceitaria o container no meio de um restart.
set -e
cd "$1"
export RELEASE_TAG="$2"
COMPOSE="docker compose -f docker-compose.prod.yml --env-file .env.prod"

for i in $(seq 1 30); do
  if $COMPOSE exec -T api curl -fsS http://localhost:8000/health < /dev/null > /dev/null 2>&1; then
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "API não respondeu em /health após 90 s. Últimas linhas do log:" >&2
    $COMPOSE logs --tail=100 api >&2
    exit 1
  fi
  sleep 3
done

total=$($COMPOSE config --services | wc -l)
running=$($COMPOSE ps --status running --services < /dev/null | wc -l)
if [ "$running" -ne "$total" ]; then
  echo "Nem todos os serviços estão rodando ($running/$total)." >&2
  $COMPOSE ps >&2
  exit 1
fi
echo "HEALTH_OK"

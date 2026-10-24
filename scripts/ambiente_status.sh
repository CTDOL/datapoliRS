#!/usr/bin/env bash
# Grava os containers ativos da stack em frontend/public/ambiente-status.json,
# lido pela barra de ambiente (EnvironmentBadge). Só dev e hml: não roda em produção.
#
# Uso: scripts/ambiente_status.sh '<regex de nomes>' [diretorio-do-frontend]
#   dev: scripts/ambiente_status.sh '_dev$|_non_prod$'
#   hml: scripts/ambiente_status.sh '_hml$|_non_prod$' /caminho/do/worktree-hml/frontend
set -euo pipefail

REGEX="${1:?uso: ambiente_status.sh '<regex de nomes>' [diretorio-do-frontend]}"
FRONT="${2:-$(cd "$(dirname "$0")/.." && pwd)/frontend}"
ALVO="$FRONT/public/ambiente-status.json"
INTERVALO="${AMBIENTE_STATUS_INTERVALO:-15}"

while true; do
  docker ps --format '{{.Names}}	{{.Status}}' \
    | awk -F'\t' -v re="$REGEX" '$1 ~ re' \
    | sort \
    | python3 -c '
import json, sys, datetime
linhas = [l.rstrip("\n") for l in sys.stdin if l.strip()]
containers = []
for linha in linhas:
    nome, _, status = linha.partition("\t")
    containers.append({"nome": nome, "status": status})
saida = {"geradoEm": datetime.datetime.now().isoformat(timespec="seconds"), "containers": containers}
print(json.dumps(saida, ensure_ascii=False))
' > "$ALVO.tmp" && mv "$ALVO.tmp" "$ALVO"
  sleep "$INTERVALO"
done

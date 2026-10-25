"""Gera o compose do ensaio a partir do compose de produção resolvido.

Entrada (stdin): saída de `docker compose config --format json`.
Saída (stdout): o mesmo compose em JSON, que o docker aceita como arquivo.

Tira só o que a CI não tem: o geoipupdate (precisa da licença MaxMind) e o frontend (build pesado,
fora do caminho que o ensaio cobre). Todo o resto segue igual ao de produção.
"""
import json
import sys

SERVICOS_FORA_DO_ENSAIO = ("geoipupdate", "frontend")

compose = json.load(sys.stdin)
for nome in SERVICOS_FORA_DO_ENSAIO:
    compose["services"].pop(nome, None)
for servico in compose["services"].values():
    dependencias = servico.get("depends_on", {})
    for nome in SERVICOS_FORA_DO_ENSAIO:
        dependencias.pop(nome, None)
json.dump(compose, sys.stdout, indent=2)

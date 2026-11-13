import uuid
from typing import Any, Dict, List
import asyncpg
from app.repositories.balcao_repository import BalcaoRepository

LIMITE_DE_ATENDIDOS = 500


class BalcaoGrafoService:
    """Grafo de correlações do gabinete: atendido, atendimento e município. O schema não tem tags."""

    @staticmethod
    async def montar(connection: asyncpg.Connection, tenantId: uuid.UUID) -> Dict[str, List[Dict[str, Any]]]:
        nos: Dict[str, Dict[str, Any]] = {}
        arestas: List[Dict[str, Any]] = []

        atendidos = await BalcaoRepository.atendidosParaGrafo(connection, tenantId, LIMITE_DE_ATENDIDOS)
        for atendido in atendidos:
            idAtendido = f"atendido:{atendido['id']}"
            nos[idAtendido] = {"id": idAtendido, "tipo": "ATENDIDO", "rotulo": atendido["nome"]}
            if atendido["municipio_id"]:
                idMunicipio = f"municipio:{atendido['municipio_id']}"
                nos[idMunicipio] = {"id": idMunicipio, "tipo": "MUNICIPIO",
                                    "rotulo": atendido["nm_municipio"] or atendido["municipio_id"]}
                arestas.append({"origem": idAtendido, "destino": idMunicipio, "tipo": "RESIDE_EM"})

        atendimentos = await BalcaoRepository.atendimentosParaGrafo(
            connection, tenantId, [a["id"] for a in atendidos]
        )
        for atendimento in atendimentos:
            idAtendimento = f"atendimento:{atendimento['id']}"
            rotulo = atendimento["protocolo"] + (" (resolvido)" if atendimento["resolvido"] else "")
            nos[idAtendimento] = {"id": idAtendimento, "tipo": "ATENDIMENTO", "rotulo": rotulo}
            arestas.append({"origem": f"atendido:{atendimento['atendido_id']}", "destino": idAtendimento,
                            "tipo": "TEM_ATENDIMENTO"})
        return {"nos": list(nos.values()), "arestas": arestas}

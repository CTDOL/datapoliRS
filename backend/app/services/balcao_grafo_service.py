import uuid
from typing import Any, Dict, List, Optional
import asyncpg
from app.repositories.balcao_repository import BalcaoRepository

LIMITE_DE_ATENDIDOS = 500


class BalcaoGrafoService:
    """Grafo de correlações não-cumulativo: atendido, atendimento, liderança ponto-focal, categoria e município."""

    @staticmethod
    async def montar(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        incluirResolvidos: bool = False,
        municipioId: Optional[str] = None,
        categoriaId: Optional[uuid.UUID] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        nos: Dict[str, Dict[str, Any]] = {}
        arestas: List[Dict[str, Any]] = []

        atendidos = await BalcaoRepository.atendidosParaGrafo(connection, tenantId, LIMITE_DE_ATENDIDOS)
        atendidosPorId = {a["id"]: a for a in atendidos}
        if municipioId:
            atendidoIdsFiltrados = [a["id"] for a in atendidos if a.get("municipio_id") == municipioId]
        else:
            atendidoIdsFiltrados = [a["id"] for a in atendidos]

        if not atendidoIdsFiltrados:
            return {"nos": [], "arestas": []}

        atendimentos = await BalcaoRepository.atendimentosParaGrafo(
            connection, tenantId, atendidoIdsFiltrados, incluirResolvidos=incluirResolvidos
        )
        liderancaIds: List[uuid.UUID] = []

        for atendimento in atendimentos:
            if categoriaId and atendimento.get("categoria_id") != categoriaId:
                continue
            atendido = atendidosPorId.get(atendimento["atendido_id"])
            if not atendido:
                continue

            idAtendido = f"atendido:{atendido['id']}"
            nos[idAtendido] = {"id": idAtendido, "tipo": "ATENDIDO", "rotulo": atendido["nome"]}
            if atendido.get("municipio_id"):
                idMunicipio = f"municipio:{atendido['municipio_id']}"
                nos[idMunicipio] = {
                    "id": idMunicipio,
                    "tipo": "MUNICIPIO",
                    "rotulo": atendido["nm_municipio"] or atendido["municipio_id"],
                }
                arestas.append({"origem": idAtendido, "destino": idMunicipio, "tipo": "RESIDE_EM"})

            idAtendimento = f"atendimento:{atendimento['id']}"
            rotulo = atendimento["protocolo"] + (" (resolvido)" if atendimento["resolvido"] else "")
            nos[idAtendimento] = {
                "id": idAtendimento,
                "tipo": "ATENDIMENTO",
                "rotulo": rotulo,
                "subtitulo": atendimento.get("intencao") or atendimento.get("categoria_nome"),
            }
            arestas.append({"origem": idAtendido, "destino": idAtendimento, "tipo": "TEM_ATENDIMENTO"})

            if atendimento.get("lideranca_ponto_focal_id"):
                lidId = atendimento["lideranca_ponto_focal_id"]
                idLideranca = f"lideranca:{lidId}"
                nos[idLideranca] = {
                    "id": idLideranca,
                    "tipo": "LIDERANCA",
                    "rotulo": atendimento.get("nm_lideranca") or "Liderança",
                    "subtitulo": atendimento.get("cargo_lideranca"),
                }
                arestas.append({"origem": idAtendimento, "destino": idLideranca, "tipo": "PONTO_FOCAL"})
                if lidId not in liderancaIds:
                    liderancaIds.append(lidId)

            if atendimento.get("categoria_id"):
                idCategoria = f"categoria:{atendimento['categoria_id']}"
                nos[idCategoria] = {
                    "id": idCategoria,
                    "tipo": "CATEGORIA",
                    "rotulo": atendimento.get("categoria_nome") or "Categoria",
                }
                arestas.append({"origem": idAtendimento, "destino": idCategoria, "tipo": "PERTENCE_A"})

        for vinculo in await BalcaoRepository.liderancasMunicipiosParaGrafo(connection, tenantId, liderancaIds):
            idLideranca = f"lideranca:{vinculo['id_lideranca']}"
            idMunicipio = f"municipio:{vinculo['cd_ibge_7']}"
            if idMunicipio not in nos:
                nos[idMunicipio] = {
                    "id": idMunicipio,
                    "tipo": "MUNICIPIO",
                    "rotulo": vinculo["nm_municipio"] or vinculo["cd_ibge_7"],
                }
            arestas.append({"origem": idLideranca, "destino": idMunicipio, "tipo": "ATUA_EM"})

        # Deduplica arestas idênticas (ex.: vários atendidos na mesma cidade ou liderança)
        vistas = set()
        arestasUnicas = []
        for a in arestas:
            chave = (a["origem"], a["destino"], a["tipo"])
            if chave not in vistas:
                vistas.add(chave)
                arestasUnicas.append(a)
        return {"nos": list(nos.values()), "arestas": arestasUnicas}

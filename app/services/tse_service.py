from typing import Optional, Dict, Any, List
import httpx
from app.schemas.candidate import CandidataDetalhada, BemDeclarado

TSE_BASE_URL = "https://divulgacandcontas.tse.jus.br/divulga/rest/v1/candidatura"
CARGO_DEPUTADO_ESTADUAL = 7


class TSEService:
    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    async def _get(self, endpoint: str) -> Optional[Dict[str, Any]]:
        url = f"{TSE_BASE_URL}/{endpoint}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url)
            if response.status_code == 200:
                return response.json()
            return None

    async def buscar_candidatas_rs(self, ano: int, codigo_eleicao: str) -> List[Dict[str, Any]]:
        # Formato correto do TSE para listar (ex: listar/2022/RS/2040602022/7/candidatos)
        dados = await self._get(f"listar/{ano}/RS/{codigo_eleicao}/{CARGO_DEPUTADO_ESTADUAL}/candidatos")
        if not dados:
            return []
        return dados.get("candidatos", [])

    async def obter_detalhes_candidato(self, ano: int, codigo_eleicao: str, id_candidato: int) -> Optional[Dict[str, Any]]:
        # Formato correto do TSE para buscar detalhes (ex: buscar/2022/RS/2040602022/candidato/210001620207)
        return await self._get(f"buscar/{ano}/RS/{codigo_eleicao}/candidato/{id_candidato}")

    async def pesquisar_deputada_rs(
        self, nome: str, ano: int, codigo_eleicao: str
    ) -> Optional[CandidataDetalhada]:
        candidatos = await self.buscar_candidatas_rs(ano, codigo_eleicao)
        termo = nome.strip().lower()

        candidata_resumo = next(
            (
                c for c in candidatos
                if c.get("cargo", {}).get("codigo") == CARGO_DEPUTADO_ESTADUAL
                and (termo in c.get("nomeUrna", "").lower() or termo in c.get("nomeCompleto", "").lower())
            ),
            None
        )

        if not candidata_resumo:
            return None

        id_candidato = candidata_resumo["id"]
        detalhes = await self.obter_detalhes_candidato(ano, codigo_eleicao, id_candidato)
        if not detalhes:
            return None

        bens = [
            BemDeclarado(
                descricao=b.get("descricaoDeBem"),
                tipo=b.get("dsTipoBemCandidato"),
                valor=float(b.get("valor", 0.0))
            )
            for b in detalhes.get("bens", [])
        ]

        return CandidataDetalhada(
            id_tse=detalhes.get("id"),
            nome_completo=detalhes.get("nomeCompleto"),
            nome_urna=detalhes.get("nomeUrna"),
            numero_urna=detalhes.get("numero"),
            sigla_uf=detalhes.get("siglaUf", "RS"),
            partido=detalhes.get("partido", {}).get("sigla", "N/I"),
            cargo=detalhes.get("cargo", {}).get("nome", "Deputado Estadual"),
            situacao_candidatura=detalhes.get("descricaoSituacao"),
            reeleicao=detalhes.get("st_REELEICAO", False),
            total_bens=float(detalhes.get("totalDeBens", 0.0) or 0.0),
            lista_bens=bens,
            foto_url=detalhes.get("fotoUrl")
        )

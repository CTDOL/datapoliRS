"""Endereços e liga/desliga das APIs externas, lidos da tela do super-admin (tb_configuracoes_sistema, categoria 'apis')."""
from typing import Dict, Optional, Set, Tuple

import asyncpg

from app.services.system_config_service import SystemConfigService

# Fontes que têm endereço configurável. A chave é o identificador usado em cada integração.
FONTES = {
    "tse": "https://divulgacandcontas.tse.jus.br/divulga/rest/v1/candidatura",
    "camara": "https://dadosabertos.camara.leg.br/api/v2",
    "senado": "https://legis.senado.leg.br/dadosabertos",
    "alrs": "https://ww4.al.rs.gov.br",
}

# Fonte legislativa (valor de tb_projeto_lei.fonte) para a chave de configuração.
FONTES_LEGISLATIVAS = {"ALRS": "alrs", "CAMARA": "camara", "SENADO": "senado"}


class ApisService:
    @staticmethod
    async def endereco(connection: asyncpg.Connection, fonte: str) -> str:
        return await SystemConfigService.getStr(connection, f"api.{fonte}.base_url", FONTES[fonte])

    @staticmethod
    async def ativa(connection: asyncpg.Connection, fonte: str) -> bool:
        return await SystemConfigService.getInt(connection, f"api.{fonte}.ativa", 1) == 1

    @staticmethod
    async def fontesLegislativas(connection: asyncpg.Connection) -> Tuple[Dict[str, str], Set[str]]:
        """Endereços por fonte legislativa e o conjunto das que estão desligadas."""
        enderecos: Dict[str, str] = {}
        desligadas: Set[str] = set()
        for fonte_legislativa, chave in FONTES_LEGISLATIVAS.items():
            enderecos[fonte_legislativa] = await ApisService.endereco(connection, chave)
            if not await ApisService.ativa(connection, chave):
                desligadas.add(fonte_legislativa)
        return enderecos, desligadas

    @staticmethod
    def enderecoValido(valor: str) -> Optional[str]:
        """Só aceita https: o endereço é usado para fazer requisições, então nada de http nem de esquemas estranhos."""
        valor = (valor or "").strip().rstrip("/")
        if not valor.startswith("https://") or len(valor) > 255 or " " in valor:
            return None
        return valor

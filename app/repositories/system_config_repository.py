import logging
from typing import Dict, List, Any
import asyncpg

logger = logging.getLogger("SystemConfigRepository")


class SystemConfigRepository:
    """Repositório das configurações globais da instância (tb_configuracoes_sistema)."""

    @staticmethod
    async def getAll(connection: asyncpg.Connection) -> List[Dict[str, Any]]:
        query = """
            SELECT chave, valor, tipo, categoria, descricao, updated_at
            FROM tb_configuracoes_sistema
            ORDER BY categoria ASC, chave ASC;
        """
        records = await connection.fetch(query)
        return [dict(record) for record in records]

    @staticmethod
    async def updateMany(connection: asyncpg.Connection, updates: Dict[str, str]) -> None:
        """Atualiza múltiplas chaves numa única transação — ou tudo aplica, ou nada."""
        try:
            async with connection.transaction():
                for chave, valor in updates.items():
                    await connection.execute(
                        "UPDATE tb_configuracoes_sistema SET valor = $1, updated_at = NOW() WHERE chave = $2;",
                        valor, chave
                    )
        except asyncpg.PostgresError as dbError:
            logger.error(f"Erro ao atualizar configurações do sistema: {dbError}", exc_info=True)
            raise RuntimeError(f"Database update error: {dbError}") from dbError

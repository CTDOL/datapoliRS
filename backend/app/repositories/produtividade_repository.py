import uuid
from typing import Any, Dict, List, Optional

import asyncpg


class ProdutividadeRepository:
    """Consultas do quadro de tarefas e do painel de produtividade. Toda consulta filtra pelo tenant."""

    @staticmethod
    async def tarefaDoTenant(connection: asyncpg.Connection, tenantId: uuid.UUID, tarefaId: uuid.UUID) -> bool:
        return await connection.fetchval(
            "SELECT EXISTS (SELECT 1 FROM tb_gabinete_tarefas WHERE tenant_id = $1 AND id_tarefa = $2)",
            tenantId, tarefaId,
        )

    @staticmethod
    async def listarComentarios(connection: asyncpg.Connection, tenantId: uuid.UUID, tarefaId: uuid.UUID) -> List[Dict[str, Any]]:
        registros = await connection.fetch(
            """
            SELECT id_comentario, id_tarefa, autor_email, texto, created_at
              FROM tb_gabinete_tarefa_comentarios
             WHERE tenant_id = $1 AND id_tarefa = $2
             ORDER BY created_at ASC
            """,
            tenantId, tarefaId,
        )
        return [dict(r) for r in registros]

    @staticmethod
    async def criarComentario(connection: asyncpg.Connection, tenantId: uuid.UUID, tarefaId: uuid.UUID,
                              autorEmail: str, texto: str) -> Dict[str, Any]:
        registro = await connection.fetchrow(
            """
            INSERT INTO tb_gabinete_tarefa_comentarios (tenant_id, id_tarefa, autor_email, texto)
            VALUES ($1, $2, $3, $4)
            RETURNING id_comentario, id_tarefa, autor_email, texto, created_at
            """,
            tenantId, tarefaId, autorEmail, texto,
        )
        return dict(registro)

    @staticmethod
    async def totaisTarefas(connection: asyncpg.Connection, tenantId: uuid.UUID) -> Dict[str, Any]:
        registro = await connection.fetchrow(
            """
            SELECT COUNT(*) AS total,
                   COUNT(*) FILTER (WHERE tp_status = 'Pendente') AS pendente,
                   COUNT(*) FILTER (WHERE tp_status = 'Em Andamento') AS em_andamento,
                   COUNT(*) FILTER (WHERE tp_status = 'Concluída') AS concluida,
                   COUNT(*) FILTER (WHERE tp_status <> 'Concluída' AND prazo < CURRENT_DATE) AS atrasadas
              FROM tb_gabinete_tarefas
             WHERE tenant_id = $1
            """,
            tenantId,
        )
        return dict(registro)

    @staticmethod
    async def cargaPorResponsavel(connection: asyncpg.Connection, tenantId: uuid.UUID) -> List[Dict[str, Any]]:
        registros = await connection.fetch(
            """
            SELECT l.nm_completo AS nome,
                   COUNT(*) FILTER (WHERE t.tp_status <> 'Concluída') AS abertas,
                   COUNT(*) FILTER (WHERE t.tp_status = 'Concluída') AS concluidas
              FROM tb_gabinete_tarefas t
              LEFT JOIN tb_gabinete_liderancas l ON l.id_lideranca = t.id_lideranca_responsavel
             WHERE t.tenant_id = $1
             GROUP BY l.nm_completo
             ORDER BY abertas DESC, nome NULLS LAST
            """,
            tenantId,
        )
        return [dict(r) for r in registros]

    @staticmethod
    async def comentariosRecentes(connection: asyncpg.Connection, tenantId: uuid.UUID) -> int:
        return await connection.fetchval(
            "SELECT COUNT(*) FROM tb_gabinete_tarefa_comentarios WHERE tenant_id = $1 AND created_at > now() - interval '7 days'",
            tenantId,
        )

    @staticmethod
    async def contar(connection: asyncpg.Connection, tenantId: uuid.UUID, tabela: str) -> int:
        # Tabela vem só de constantes do próprio código, nunca da requisição.
        return await connection.fetchval(f"SELECT COUNT(*) FROM {tabela} WHERE tenant_id = $1", tenantId)

import json
import uuid
from typing import Any, Dict, List, Optional
import asyncpg


def _json(valor: Any) -> Dict[str, Any]:
    """O asyncpg devolve jsonb como texto."""
    if isinstance(valor, str):
        return json.loads(valor)
    return dict(valor or {})


def _entrada(registro: asyncpg.Record) -> Dict[str, Any]:
    dados = dict(registro)
    dados["dados_extraidos_json"] = _json(dados.get("dados_extraidos_json"))
    dados["dados_extraidos"] = dados["dados_extraidos_json"]
    return dados


class BalcaoRepository:
    """Repositório do Balcão Inteligente. Todo SQL filtra por tenant_id, inclusive nas tabelas filhas.

    Única exceção: resolverPortalPorTokenHash, que é de onde o tenant_id da rota pública passa a vir.
    """

    # --- Portais -----------------------------------------------------------------------------

    @staticmethod
    async def resolverPortalPorTokenHash(connection: asyncpg.Connection, tokenHash: str) -> Optional[Dict[str, Any]]:
        registro = await connection.fetchrow(
            "SELECT id, tenant_id FROM tb_balcao_portais WHERE token_hash = $1 AND ativo = TRUE",
            tokenHash,
        )
        return dict(registro) if registro else None

    @staticmethod
    async def criarPortal(connection: asyncpg.Connection, tenantId: uuid.UUID, tokenHash: str) -> Dict[str, Any]:
        registro = await connection.fetchrow(
            """INSERT INTO tb_balcao_portais (tenant_id, token_hash) VALUES ($1, $2)
               RETURNING id, ativo, criado_em""",
            tenantId, tokenHash,
        )
        return dict(registro)

    @staticmethod
    async def listarPortais(connection: asyncpg.Connection, tenantId: uuid.UUID) -> List[Dict[str, Any]]:
        registros = await connection.fetch(
            "SELECT id, ativo, criado_em FROM tb_balcao_portais WHERE tenant_id = $1 ORDER BY criado_em DESC",
            tenantId,
        )
        return [dict(r) for r in registros]

    @staticmethod
    async def revogarPortal(connection: asyncpg.Connection, tenantId: uuid.UUID, portalId: uuid.UUID) -> Optional[Dict[str, Any]]:
        registro = await connection.fetchrow(
            "UPDATE tb_balcao_portais SET ativo = FALSE WHERE tenant_id = $1 AND id = $2 RETURNING id, ativo",
            tenantId, portalId,
        )
        return dict(registro) if registro else None

    # --- Entradas ----------------------------------------------------------------------------

    @staticmethod
    async def criarEntrada(connection: asyncpg.Connection, tenantId: uuid.UUID, portalId: uuid.UUID,
                           texto: str, sha256Texto: str) -> Dict[str, Any]:
        registro = await connection.fetchrow(
            """INSERT INTO tb_balcao_entradas (tenant_id, portal_id, texto_original, sha256_texto)
               VALUES ($1, $2, $3, $4)
               RETURNING id, tenant_id, status, texto_original, dados_extraidos_json, criado_em""",
            tenantId, portalId, texto, sha256Texto,
        )
        return _entrada(registro)

    @staticmethod
    async def listarEntradas(connection: asyncpg.Connection, tenantId: uuid.UUID,
                             status: Optional[str]) -> List[Dict[str, Any]]:
        registros = await connection.fetch(
            """SELECT id, tenant_id, status, texto_original, dados_extraidos_json, criado_em
                 FROM tb_balcao_entradas
                WHERE tenant_id = $1 AND ($2::text IS NULL OR status = $2)
                ORDER BY criado_em DESC
                LIMIT 200""",
            tenantId, status,
        )
        return [_entrada(r) for r in registros]

    @staticmethod
    async def obterEntrada(connection: asyncpg.Connection, tenantId: uuid.UUID, entradaId: uuid.UUID,
                           paraAtualizar: bool = False) -> Optional[Dict[str, Any]]:
        trava = " FOR UPDATE" if paraAtualizar else ""
        registro = await connection.fetchrow(
            """SELECT id, tenant_id, portal_id, status, texto_original, sha256_texto, dados_extraidos_json, criado_em
                 FROM tb_balcao_entradas WHERE tenant_id = $1 AND id = $2""" + trava,
            tenantId, entradaId,
        )
        return _entrada(registro) if registro else None

    @staticmethod
    async def gravarDadosExtraidos(connection: asyncpg.Connection, tenantId: uuid.UUID, entradaId: uuid.UUID,
                                   dados: Dict[str, Any]) -> None:
        await connection.execute(
            "UPDATE tb_balcao_entradas SET dados_extraidos_json = $3::jsonb WHERE tenant_id = $1 AND id = $2",
            tenantId, entradaId, json.dumps(dados),
        )

    @staticmethod
    async def efetivarEntrada(connection: asyncpg.Connection, tenantId: uuid.UUID, entradaId: uuid.UUID,
                              resumo: str, efetivacao: Dict[str, Any]) -> None:
        """O texto bruto do cidadão dá lugar ao resumo autorizado (ADR_011 APEX); o hash é preservado."""
        await connection.execute(
            """UPDATE tb_balcao_entradas
                  SET status = 'EFETIVADA',
                      texto_original = $3,
                      dados_extraidos_json = dados_extraidos_json || $4::jsonb
                WHERE tenant_id = $1 AND id = $2""",
            tenantId, entradaId, resumo, json.dumps({"efetivacao": efetivacao}),
        )

    @staticmethod
    async def descartarEntrada(connection: asyncpg.Connection, tenantId: uuid.UUID, entradaId: uuid.UUID,
                               descarte: Dict[str, Any]) -> None:
        """Texto bruto vira string vazia e os dados extraídos dão lugar ao registro do descarte."""
        await connection.execute(
            """UPDATE tb_balcao_entradas
                  SET status = 'DESCARTADA', texto_original = '', dados_extraidos_json = $3::jsonb
                WHERE tenant_id = $1 AND id = $2""",
            tenantId, entradaId, json.dumps({"descarte": descarte}),
        )

    # --- Duplicidade e alerta de assunto resolvido -------------------------------------------

    @staticmethod
    async def entradasComMesmoHash(connection: asyncpg.Connection, tenantId: uuid.UUID, sha256Texto: str,
                                   ignorarId: uuid.UUID) -> List[uuid.UUID]:
        registros = await connection.fetch(
            """SELECT id FROM tb_balcao_entradas
                WHERE tenant_id = $1 AND sha256_texto = $2 AND id <> $3
                ORDER BY criado_em DESC LIMIT 5""",
            tenantId, sha256Texto, ignorarId,
        )
        return [r["id"] for r in registros]

    @staticmethod
    async def entradasSimilares(connection: asyncpg.Connection, tenantId: uuid.UUID, texto: str,
                                limiar: float, ignorarIds: List[uuid.UUID]) -> List[Dict[str, Any]]:
        registros = await connection.fetch(
            """SELECT id, similarity(texto_original, $2::text) AS score
                 FROM tb_balcao_entradas
                WHERE tenant_id = $1 AND NOT (id = ANY($4::uuid[]))
                  AND similarity(texto_original, $2::text) >= $3::real
                ORDER BY score DESC LIMIT 5""",
            tenantId, texto, limiar, ignorarIds,
        )
        return [dict(r) for r in registros]

    @staticmethod
    async def entradasPorContato(connection: asyncpg.Connection, tenantId: uuid.UUID,
                                 telefone: Optional[str], email: Optional[str], cpfHash: Optional[str],
                                 ignorarIds: List[uuid.UUID]) -> List[uuid.UUID]:
        if not any((telefone, email, cpfHash)):
            return []
        registros = await connection.fetch(
            """SELECT id FROM tb_balcao_entradas
                WHERE tenant_id = $1 AND status != 'DESCARTADA'
                  AND NOT (id = ANY($5::uuid[]))
                  AND (
                    ($2::text IS NOT NULL AND dados_extraidos_json->>'telefone' = $2::text)
                    OR ($3::text IS NOT NULL AND dados_extraidos_json->>'email' = $3::text)
                    OR ($4::text IS NOT NULL AND dados_extraidos_json->>'cpf_hash' = $4::text)
                  )
                ORDER BY criado_em DESC LIMIT 5""",
            tenantId, telefone, email, cpfHash, ignorarIds,
        )
        return [r["id"] for r in registros]

    @staticmethod
    async def atendimentosResolvidosSimilares(connection: asyncpg.Connection, tenantId: uuid.UUID, texto: str,
                                              limiar: float, dias: int) -> List[Dict[str, Any]]:
        registros = await connection.fetch(
            """SELECT DISTINCT ON (a.id) a.id, similarity(a.resumo, $2::text) AS score
                 FROM tb_atendimentos a
                 JOIN tb_balcao_resolucoes r ON r.tenant_id = a.tenant_id AND r.atendimento_id = a.id
                WHERE a.tenant_id = $1
                  AND r.resolvido_em >= now() - make_interval(days => $4::int)
                  AND similarity(a.resumo, $2::text) >= $3::real
                ORDER BY a.id, score DESC""",
            tenantId, texto, limiar, dias,
        )
        return sorted((dict(r) for r in registros), key=lambda r: r["score"], reverse=True)[:5]

    @staticmethod
    async def criarSugestao(connection: asyncpg.Connection, tenantId: uuid.UUID, entradaId: uuid.UUID,
                            entradaSimilarId: Optional[uuid.UUID], atendimentoRelacionadoId: Optional[uuid.UUID],
                            score: float, motivo: str) -> None:
        await connection.execute(
            """INSERT INTO tb_balcao_sugestoes
                   (tenant_id, entrada_id, entrada_similar_id, atendimento_relacionado_id, score_similaridade, motivo)
               VALUES ($1, $2, $3, $4, $5, $6)""",
            tenantId, entradaId, entradaSimilarId, atendimentoRelacionadoId, round(score, 3), motivo,
        )

    @staticmethod
    async def listarSugestoes(connection: asyncpg.Connection, tenantId: uuid.UUID,
                              entradaId: uuid.UUID) -> List[Dict[str, Any]]:
        registros = await connection.fetch(
            """SELECT id, entrada_similar_id, atendimento_relacionado_id,
                      score_similaridade::float AS score_similaridade, motivo
                 FROM tb_balcao_sugestoes
                WHERE tenant_id = $1 AND entrada_id = $2
                ORDER BY score_similaridade DESC, criado_em""",
            tenantId, entradaId,
        )
        return [dict(r) for r in registros]

    @staticmethod
    async def excluirAnexosDaEntrada(connection: asyncpg.Connection, tenantId: uuid.UUID,
                                     entradaId: uuid.UUID) -> List[str]:
        registros = await connection.fetch(
            """DELETE FROM tb_balcao_anexos
                WHERE tenant_id = $1 AND entrada_id = $2 AND atendimento_id IS NULL
                RETURNING caminho_arquivo""",
            tenantId, entradaId,
        )
        return [r["caminho_arquivo"] for r in registros]

    # --- Atendidos e atendimentos ------------------------------------------------------------

    @staticmethod
    async def obterAtendido(connection: asyncpg.Connection, tenantId: uuid.UUID,
                            atendidoId: uuid.UUID) -> Optional[Dict[str, Any]]:
        registro = await connection.fetchrow(
            "SELECT id, nome, municipio_id FROM tb_atendidos WHERE tenant_id = $1 AND id = $2",
            tenantId, atendidoId,
        )
        return dict(registro) if registro else None

    @staticmethod
    async def obterAtendidoPorCpfHash(connection: asyncpg.Connection, tenantId: uuid.UUID,
                                      cpfHash: str) -> Optional[Dict[str, Any]]:
        registro = await connection.fetchrow(
            "SELECT id, nome, municipio_id FROM tb_atendidos WHERE tenant_id = $1 AND cpf_hash = $2",
            tenantId, cpfHash,
        )
        return dict(registro) if registro else None

    @staticmethod
    async def criarAtendido(connection: asyncpg.Connection, tenantId: uuid.UUID, nome: str, cpfHash: Optional[str],
                            telefone: Optional[str], email: Optional[str],
                            municipioId: Optional[str]) -> Dict[str, Any]:
        registro = await connection.fetchrow(
            """INSERT INTO tb_atendidos (tenant_id, nome, cpf_hash, telefone, email, municipio_id)
               VALUES ($1, $2, $3, $4, $5, $6)
               RETURNING id, nome, municipio_id""",
            tenantId, nome, cpfHash, telefone, email, municipioId,
        )
        return dict(registro)

    @staticmethod
    async def proximoProtocolo(connection: asyncpg.Connection, tenantId: uuid.UUID) -> str:
        """BAL-AAAA-NNNNNN sequencial por gabinete e ano. Deve rodar dentro da transação da efetivação:
        o advisory lock por (gabinete, ano) serializa o MAX+1 e é solto no commit. A unique
        (tenant_id, protocolo) do schema é a rede de segurança."""
        await connection.execute(
            "SELECT pg_advisory_xact_lock(hashtext($1::text), EXTRACT(YEAR FROM now())::int)",
            str(tenantId),
        )
        return await connection.fetchval(
            """WITH ano AS (SELECT EXTRACT(YEAR FROM now())::int AS valor)
               SELECT 'BAL-' || ano.valor || '-'
                      || lpad((COALESCE(MAX(substring(t.protocolo FROM 10 FOR 6)::int), 0) + 1)::text, 6, '0')
                 FROM ano
                 LEFT JOIN tb_atendimentos t
                        ON t.tenant_id = $1 AND t.protocolo LIKE 'BAL-' || ano.valor || '-%'
                GROUP BY ano.valor""",
            tenantId,
        )

    @staticmethod
    async def criarAtendimento(connection: asyncpg.Connection, tenantId: uuid.UUID, atendidoId: uuid.UUID,
                               protocolo: str, tipoEvento: str, resumo: str,
                               userId: Optional[uuid.UUID]) -> Dict[str, Any]:
        registro = await connection.fetchrow(
            """INSERT INTO tb_atendimentos (tenant_id, atendido_id, protocolo, tipo_evento, resumo, criado_por_user_id)
               VALUES ($1, $2, $3, $4, $5, $6)
               RETURNING id, atendido_id, protocolo""",
            tenantId, atendidoId, protocolo, tipoEvento, resumo, userId,
        )
        return dict(registro)

    @staticmethod
    async def obterAtendimento(connection: asyncpg.Connection, tenantId: uuid.UUID,
                               atendimentoId: uuid.UUID) -> Optional[Dict[str, Any]]:
        registro = await connection.fetchrow(
            "SELECT id, atendido_id, protocolo FROM tb_atendimentos WHERE tenant_id = $1 AND id = $2",
            tenantId, atendimentoId,
        )
        return dict(registro) if registro else None

    @staticmethod
    async def listarAtendimentosDoAtendido(connection: asyncpg.Connection, tenantId: uuid.UUID,
                                           atendidoId: uuid.UUID) -> List[Dict[str, Any]]:
        registros = await connection.fetch(
            """SELECT id, protocolo, tipo_evento, resumo, criado_em
                 FROM tb_atendimentos WHERE tenant_id = $1 AND atendido_id = $2
                ORDER BY criado_em, protocolo""",
            tenantId, atendidoId,
        )
        return [dict(r) for r in registros]

    @staticmethod
    async def listarResolucoesDoAtendido(connection: asyncpg.Connection, tenantId: uuid.UUID,
                                         atendidoId: uuid.UUID) -> List[Dict[str, Any]]:
        registros = await connection.fetch(
            """SELECT r.id, r.despacho, r.resolvido_em
                 FROM tb_balcao_resolucoes r
                 JOIN tb_atendimentos a ON a.tenant_id = r.tenant_id AND a.id = r.atendimento_id
                WHERE r.tenant_id = $1 AND a.atendido_id = $2
                ORDER BY r.resolvido_em""",
            tenantId, atendidoId,
        )
        return [dict(r) for r in registros]

    # --- Anexos ------------------------------------------------------------------------------

    @staticmethod
    async def criarAnexo(connection: asyncpg.Connection, tenantId: uuid.UUID, entradaId: Optional[uuid.UUID],
                         atendimentoId: Optional[uuid.UUID], caminhoArquivo: str, sha256Arquivo: str,
                         mimeType: str, tamanhoBytes: int) -> Dict[str, Any]:
        registro = await connection.fetchrow(
            """INSERT INTO tb_balcao_anexos
                   (tenant_id, entrada_id, atendimento_id, caminho_arquivo, sha256_arquivo, mime_type, tamanho_bytes)
               VALUES ($1, $2, $3, $4, $5, $6, $7)
               RETURNING id, mime_type, tamanho_bytes""",
            tenantId, entradaId, atendimentoId, caminhoArquivo, sha256Arquivo, mimeType, tamanhoBytes,
        )
        return dict(registro)

    @staticmethod
    async def obterAnexo(connection: asyncpg.Connection, tenantId: uuid.UUID,
                         anexoId: uuid.UUID) -> Optional[Dict[str, Any]]:
        registro = await connection.fetchrow(
            """SELECT id, caminho_arquivo, mime_type, tamanho_bytes
                 FROM tb_balcao_anexos WHERE tenant_id = $1 AND id = $2""",
            tenantId, anexoId,
        )
        return dict(registro) if registro else None

    @staticmethod
    async def listarAnexosDaEntrada(connection: asyncpg.Connection, tenantId: uuid.UUID,
                                    entradaId: uuid.UUID) -> List[Dict[str, Any]]:
        registros = await connection.fetch(
            """SELECT id, mime_type, tamanho_bytes FROM tb_balcao_anexos
                WHERE tenant_id = $1 AND entrada_id = $2 ORDER BY criado_em""",
            tenantId, entradaId,
        )
        return [dict(r) for r in registros]

    @staticmethod
    async def obterAnexoDoAtendimento(connection: asyncpg.Connection, tenantId: uuid.UUID, anexoId: uuid.UUID,
                                      atendimentoId: uuid.UUID) -> Optional[Dict[str, Any]]:
        registro = await connection.fetchrow(
            """SELECT id FROM tb_balcao_anexos
                WHERE tenant_id = $1 AND id = $2 AND atendimento_id = $3""",
            tenantId, anexoId, atendimentoId,
        )
        return dict(registro) if registro else None

    # --- Resolução ---------------------------------------------------------------------------

    @staticmethod
    async def criarResolucao(connection: asyncpg.Connection, tenantId: uuid.UUID, atendimentoId: uuid.UUID,
                             despacho: str, evidenciaAnexoId: uuid.UUID, userId: uuid.UUID) -> Dict[str, Any]:
        registro = await connection.fetchrow(
            """INSERT INTO tb_balcao_resolucoes
                   (tenant_id, atendimento_id, despacho, evidencia_anexo_id, resolvido_por_user_id)
               VALUES ($1, $2, $3, $4, $5)
               RETURNING id, atendimento_id, resolvido_em""",
            tenantId, atendimentoId, despacho, evidenciaAnexoId, userId,
        )
        return dict(registro)

    # --- Grafo -------------------------------------------------------------------------------

    @staticmethod
    async def atendidosParaGrafo(connection: asyncpg.Connection, tenantId: uuid.UUID, limite: int) -> List[Dict[str, Any]]:
        registros = await connection.fetch(
            """SELECT a.id, a.nome, a.municipio_id, m.nm_municipio
                 FROM tb_atendidos a
                 LEFT JOIN tb_municipios m ON m.cd_ibge_7 = a.municipio_id
                WHERE a.tenant_id = $1
                ORDER BY a.criado_em DESC LIMIT $2""",
            tenantId, limite,
        )
        return [dict(r) for r in registros]

    @staticmethod
    async def atendimentosParaGrafo(connection: asyncpg.Connection, tenantId: uuid.UUID,
                                    atendidoIds: List[uuid.UUID]) -> List[Dict[str, Any]]:
        registros = await connection.fetch(
            """SELECT t.id, t.atendido_id, t.protocolo,
                      EXISTS (SELECT 1 FROM tb_balcao_resolucoes r
                               WHERE r.tenant_id = t.tenant_id AND r.atendimento_id = t.id) AS resolvido
                 FROM tb_atendimentos t
                WHERE t.tenant_id = $1 AND t.atendido_id = ANY($2::uuid[])
                ORDER BY t.criado_em""",
            tenantId, atendidoIds,
        )
        return [dict(r) for r in registros]

    @staticmethod
    async def listarPedidosMapa(connection: asyncpg.Connection, tenantId: uuid.UUID) -> List[Dict[str, Any]]:
        pendentes = await connection.fetch(
            """SELECT e.id,
                      'PENDENTE'::text AS tipo,
                      LEFT(e.texto_original, 140) AS resumo,
                      e.dados_extraidos_json->>'nome' AS nome_atendido,
                      m.cd_ibge_7 AS municipio_id,
                      m.nm_municipio AS municipio_nome,
                      ST_Y(ST_Centroid(m.geometria))::float AS latitude,
                      ST_X(ST_Centroid(m.geometria))::float AS longitude,
                      e.criado_em
                 FROM tb_balcao_entradas e
                 JOIN tb_municipios m ON m.cd_ibge_7 = e.dados_extraidos_json->>'municipio_id'
                WHERE e.tenant_id = $1
                  AND e.status = 'PENDENTE'
                  AND m.geometria IS NOT NULL
                  AND NOT EXISTS (
                      SELECT 1 FROM tb_balcao_sugestoes s
                       WHERE s.tenant_id = e.tenant_id
                         AND s.entrada_id = e.id
                         AND s.atendimento_relacionado_id IS NOT NULL
                  )
                ORDER BY e.criado_em DESC""",
            tenantId,
        )
        emAndamento = await connection.fetch(
            """SELECT t.id,
                      'EM_ANDAMENTO'::text AS tipo,
                      LEFT(t.resumo, 140) AS resumo,
                      a.nome AS nome_atendido,
                      m.cd_ibge_7 AS municipio_id,
                      m.nm_municipio AS municipio_nome,
                      ST_Y(ST_Centroid(m.geometria))::float AS latitude,
                      ST_X(ST_Centroid(m.geometria))::float AS longitude,
                      t.criado_em
                 FROM tb_atendimentos t
                 JOIN tb_atendidos a ON a.tenant_id = t.tenant_id AND a.id = t.atendido_id
                 JOIN tb_municipios m ON m.cd_ibge_7 = a.municipio_id
                WHERE t.tenant_id = $1
                  AND NOT EXISTS (
                      SELECT 1 FROM tb_balcao_resolucoes r
                       WHERE r.tenant_id = t.tenant_id AND r.atendimento_id = t.id
                  )
                  AND m.geometria IS NOT NULL
                ORDER BY t.criado_em DESC""",
            tenantId,
        )
        itens = [dict(r) for r in pendentes] + [dict(r) for r in emAndamento]
        itens.sort(key=lambda item: item["criado_em"], reverse=True)
        return itens

    @staticmethod
    async def listarAtendimentosAbertosResumo(
        connection: asyncpg.Connection, tenantId: uuid.UUID, limite: int = 15
    ) -> List[Dict[str, Any]]:
        registros = await connection.fetch(
            """SELECT t.id, LEFT(t.resumo, 200) AS resumo
                 FROM tb_atendimentos t
                WHERE t.tenant_id = $1
                  AND NOT EXISTS (
                      SELECT 1 FROM tb_balcao_resolucoes r
                       WHERE r.tenant_id = t.tenant_id AND r.atendimento_id = t.id
                  )
                ORDER BY t.criado_em DESC
                LIMIT $2""",
            tenantId, limite,
        )
        return [dict(r) for r in registros]

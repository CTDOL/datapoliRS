import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import asyncpg
from fastapi import status
from app.core.exceptions import DomainException
from app.repositories.balcao_repository import BalcaoRepository
from app.schemas.balcao import DescartarRequest, EfetivarRequest
from app.schemas.user import UserInDB
from app.services.balcao_anexo_service import BalcaoAnexoService
from app.services.balcao_ia_service import BalcaoIaService
from app.services.balcao_triagem_service import (
    BalcaoTriagemService,
    classificarCategoriaRegex,
    extrairDados,
    municipioUnico,
    slugificarCategoria,
)

STATUS_VALIDOS = ("PENDENTE", "EFETIVADA", "DESCARTADA")
RESUMO_MAXIMO = 5000
MOTIVO_MAXIMO = 1000


def _naoEncontrado(o_que: str) -> DomainException:
    return DomainException(f"{o_que} não encontrado.", status.HTTP_404_NOT_FOUND, "Não encontrado")


def _invalido(detalhe: str) -> DomainException:
    return DomainException(detalhe, status.HTTP_422_UNPROCESSABLE_ENTITY, "Dados inválidos")


def _limpo(valor: Optional[str]) -> Optional[str]:
    valor = (valor or "").strip()
    return valor or None


class BalcaoCaixaService:
    """Caixa de entrada: leitura, efetivação, descarte, timeline e anexos do atendimento."""

    @staticmethod
    async def listarEntradas(connection: asyncpg.Connection, tenantId: uuid.UUID,
                             status_: Optional[str]) -> List[Dict[str, Any]]:
        filtro = status_.strip().upper() if status_ else None
        if filtro is not None and filtro not in STATUS_VALIDOS:
            raise _invalido(f"Status inválido. Use um destes: {', '.join(STATUS_VALIDOS)}.")
        return await BalcaoRepository.listarEntradas(connection, tenantId, filtro)

    @staticmethod
    async def listarPedidosMapa(connection: asyncpg.Connection, tenantId: uuid.UUID) -> List[Dict[str, Any]]:
        return await BalcaoRepository.listarPedidosMapa(connection, tenantId)

    @staticmethod
    async def listarLiderancasSugeridas(
        connection: asyncpg.Connection,
        tenantId: uuid.UUID,
        municipioId: Optional[str],
    ) -> Dict[str, List[Dict[str, Any]]]:
        todas = await BalcaoRepository.listarLiderancasParaBalcao(
            connection, tenantId, municipioId.strip() if municipioId else None
        )
        return {
            "no_municipio": [l for l in todas if l["vinculada_municipio"]],
            "outras_do_gabinete": [l for l in todas if not l["vinculada_municipio"]],
        }

    @staticmethod
    async def listarCategorias(connection: asyncpg.Connection, tenantId: uuid.UUID) -> List[Dict[str, Any]]:
        return await BalcaoRepository.listarCategorias(connection, tenantId)

    @staticmethod
    async def obterEntrada(connection: asyncpg.Connection, tenantId: uuid.UUID,
                           entradaId: uuid.UUID) -> Dict[str, Any]:
        entrada = await BalcaoRepository.obterEntrada(connection, tenantId, entradaId)
        if entrada is None:
            raise _naoEncontrado("Entrada")
        entrada["sugestoes"] = await BalcaoRepository.listarSugestoes(connection, tenantId, entradaId)
        entrada["anexos"] = await BalcaoRepository.listarAnexosDaEntrada(connection, tenantId, entradaId)
        return entrada

    @staticmethod
    async def analisarEntrada(connection: asyncpg.Connection, tenantId: uuid.UUID,
                              entradaId: uuid.UUID) -> Dict[str, Any]:
        """Reexecuta a extração determinística (Regex) e, se houver provedor IA ativo em runtime,
        complementa nome e município vazios sem sobrescrever o que o regex já identificou."""
        entrada = await BalcaoRepository.obterEntrada(connection, tenantId, entradaId)
        if entrada is None:
            raise _naoEncontrado("Entrada")
        if entrada["status"] != "PENDENTE":
            raise DomainException("A entrada já foi tratada.", status.HTTP_409_CONFLICT, "Conflito")

        municipios = await BalcaoTriagemService.listarMunicipios(connection)
        categoriasExistentes = await BalcaoRepository.listarCategorias(connection, tenantId)
        dados = extrairDados(entrada["texto_original"], municipios)
        catRegex = classificarCategoriaRegex(entrada["texto_original"], categoriasExistentes)
        if catRegex:
            dados["categoria"] = catRegex

        configIa = await BalcaoIaService.obterConfiguracao(connection)
        dados["motor_usado"] = configIa.get("provider") or "regex"
        dados["motor_modelo"] = configIa.get("model") or ""

        vazios = [
            c
            for c, chave in (
                ("nome", "nome"),
                ("municipio", "municipio_id"),
                ("resumo_sugerido", "resumo_sugerido"),
                ("categoria", "categoria"),
                ("intencao", "intencao"),
            )
            if not dados.get(chave)
        ]
        if vazios and configIa.get("provider") not in ("", "regex"):
            sugeridos = await BalcaoIaService.complementar(
                entrada["texto_original"],
                vazios,
                configRuntime=configIa,
                connection=connection,
                categoriasExistentes=[c["nome"] for c in categoriasExistentes],
            )
            if "nome" in sugeridos and not dados.get("nome"):
                dados["nome"] = sugeridos["nome"]
                dados["ia_complementou"] = True
            if "municipio" in sugeridos and not dados.get("municipio_id"):
                munId = municipioUnico(sugeridos["municipio"], municipios)
                if munId:
                    dados["municipio_id"] = munId
                    dados["ia_complementou"] = True
            if "resumo_sugerido" in sugeridos and not dados.get("resumo_sugerido"):
                dados["resumo_sugerido"] = sugeridos["resumo_sugerido"]
                dados["ia_complementou"] = True
            if "categoria" in sugeridos and not dados.get("categoria"):
                dados["categoria"] = sugeridos["categoria"]
                dados["ia_complementou"] = True
            if "intencao" in sugeridos and not dados.get("intencao"):
                dados["intencao"] = sugeridos["intencao"]
                dados["ia_complementou"] = True

        if configIa.get("provider") not in ("", "regex"):
            candidatos = await BalcaoRepository.listarAtendimentosAbertosResumo(connection, tenantId)
            semelhante = await BalcaoIaService.detectarSemelhancaSemantica(
                entrada["texto_original"], candidatos, configIa, connection=connection
            )
            if semelhante:
                existentes = await BalcaoRepository.listarSugestoes(connection, tenantId, entradaId)
                jaVinculado = {str(s.get("atendimento_relacionado_id")) for s in existentes if s.get("atendimento_relacionado_id")}
                if semelhante["atendimento_id"] not in jaVinculado:
                    await BalcaoRepository.criarSugestao(
                        connection,
                        tenantId,
                        entradaId,
                        None,
                        uuid.UUID(semelhante["atendimento_id"]),
                        0.9,
                        f"SEMELHANCA_IA: {semelhante['motivo']}",
                    )

        await BalcaoRepository.gravarDadosExtraidos(connection, tenantId, entradaId, dados)
        return await BalcaoCaixaService.obterEntrada(connection, tenantId, entradaId)

    @staticmethod
    async def efetivar(connection: asyncpg.Connection, usuario: UserInDB, entradaId: uuid.UUID,
                       dados: EfetivarRequest) -> Dict[str, Any]:
        tenantId = usuario.tenant_id
        resumo = _limpo(dados.resumo)
        if resumo is None or len(resumo) > RESUMO_MAXIMO:
            raise _invalido(f"Informe o resumo do atendimento, com até {RESUMO_MAXIMO} caracteres.")

        entrada = await BalcaoRepository.obterEntrada(connection, tenantId, entradaId)
        if entrada is None:
            raise _naoEncontrado("Entrada")
        if entrada["status"] != "PENDENTE":
            raise DomainException("A entrada já foi tratada.", status.HTTP_409_CONFLICT, "Conflito")

        if dados.lideranca_ponto_focal_id is not None:
            lideranca = await BalcaoRepository.liderancaPertenceAoTenant(
                connection, tenantId, dados.lideranca_ponto_focal_id
            )
            if lideranca is None:
                raise _invalido("Liderança ponto-focal não encontrada neste gabinete.")

        campos = None
        if dados.atendido_id is None:
            campos = await BalcaoCaixaService._camposDoAtendido(connection, entrada, dados)

        extraidos = entrada["dados_extraidos_json"] or {}
        categoriaNome = _limpo(dados.categoria) or _limpo(extraidos.get("categoria"))
        intencaoTexto = _limpo(dados.intencao) or _limpo(extraidos.get("intencao"))

        async with connection.transaction():
            # Relê com trava: duas efetivações da mesma entrada não passam juntas.
            entrada = await BalcaoRepository.obterEntrada(connection, tenantId, entradaId, paraAtualizar=True)
            if entrada["status"] != "PENDENTE":
                raise DomainException("A entrada já foi tratada.", status.HTTP_409_CONFLICT, "Conflito")

            if dados.atendido_id is not None:
                atendido = await BalcaoRepository.obterAtendido(connection, tenantId, dados.atendido_id)
                if atendido is None:
                    raise _naoEncontrado("Atendido")
            else:
                atendido = None
                if campos["cpf_hash"]:
                    atendido = await BalcaoRepository.obterAtendidoPorCpfHash(connection, tenantId, campos["cpf_hash"])
                if atendido is None:
                    atendido = await BalcaoRepository.criarAtendido(
                        connection, tenantId, campos["nome"], campos["cpf_hash"], campos["telefone"],
                        campos["email"], campos["municipio_id"],
                    )

            categoriaId = None
            if categoriaNome:
                palavras = [p for p in resumo.lower().split() if len(p) >= 4][:8]
                cat = await BalcaoRepository.garantirCategoria(
                    connection,
                    tenantId,
                    categoriaNome[:100],
                    slugificarCategoria(categoriaNome),
                    palavrasChave=palavras,
                    criadaPorIa=bool(extraidos.get("ia_complementou")),
                )
                categoriaId = cat["id"]

            protocolo = await BalcaoRepository.proximoProtocolo(connection, tenantId)
            atendimento = await BalcaoRepository.criarAtendimento(
                connection,
                tenantId,
                atendido["id"],
                protocolo,
                "EFETIVACAO",
                resumo,
                usuario.id,
                liderancaPontoFocalId=dados.lideranca_ponto_focal_id,
                categoriaId=categoriaId,
                intencao=intencaoTexto[:200] if intencaoTexto else None,
            )
            await BalcaoRepository.efetivarEntrada(connection, tenantId, entradaId, resumo, {
                "atendimento_id": str(atendimento["id"]),
                "atendido_id": str(atendido["id"]),
                "protocolo": protocolo,
                "lideranca_ponto_focal_id": str(dados.lideranca_ponto_focal_id) if dados.lideranca_ponto_focal_id else None,
                "categoria_id": str(categoriaId) if categoriaId else None,
                "intencao": intencaoTexto,
                "por_user_id": str(usuario.id),
                "em": datetime.now(timezone.utc).isoformat(),
            })
        return {"atendimento_id": atendimento["id"], "atendido_id": atendido["id"], "protocolo": protocolo}

    @staticmethod
    async def atualizarPontoFocal(
        connection: asyncpg.Connection,
        usuario: UserInDB,
        atendimentoId: uuid.UUID,
        liderancaId: Optional[uuid.UUID],
    ) -> Dict[str, Any]:
        tenantId = usuario.tenant_id
        atendimento = await BalcaoRepository.obterAtendimento(connection, tenantId, atendimentoId)
        if atendimento is None:
            raise _naoEncontrado("Atendimento")
        liderancaNome = None
        if liderancaId is not None:
            lideranca = await BalcaoRepository.liderancaPertenceAoTenant(connection, tenantId, liderancaId)
            if lideranca is None:
                raise _invalido("Liderança ponto-focal não encontrada neste gabinete.")
            liderancaNome = lideranca["nm_completo"]
        novoEvento = await BalcaoRepository.atualizarPontoFocalAtendimento(
            connection, tenantId, atendimento, liderancaId, liderancaNome, usuario.id
        )
        return {
            "atendimento_id": novoEvento["id"],
            "lideranca_ponto_focal_id": liderancaId,
            "lideranca_nome": liderancaNome,
        }

    @staticmethod
    async def _camposDoAtendido(connection: asyncpg.Connection, entrada: Dict[str, Any],
                                dados: EfetivarRequest) -> Dict[str, Any]:
        """Dados informados pelo operador valem mais que os extraídos; a IA, se ligada, só preenche vazio."""
        extraidos = entrada["dados_extraidos_json"]
        municipios = await BalcaoTriagemService.listarMunicipios(connection)
        idsDeMunicipio = {m["cd_ibge_7"] for m in municipios}

        campos = {
            "nome": _limpo(dados.nome) or extraidos.get("nome"),
            "telefone": _limpo(dados.telefone) or extraidos.get("telefone"),
            "email": _limpo(dados.email) or extraidos.get("email"),
            "municipio_id": _limpo(dados.municipio_id) or extraidos.get("municipio_id"),
            "cpf_hash": extraidos.get("cpf_hash"),
        }
        if dados.municipio_id and _limpo(dados.municipio_id) not in idsDeMunicipio:
            raise _invalido("Município inválido.")

        vazios = [c for c, chave in (("nome", "nome"), ("municipio", "municipio_id")) if not campos[chave]]
        if vazios:
            configIa = await BalcaoIaService.obterConfiguracao(connection)
            sugeridos = await BalcaoIaService.complementar(
                entrada["texto_original"], vazios, configRuntime=configIa, connection=connection
            )
            if "nome" in sugeridos and not campos["nome"]:
                campos["nome"] = sugeridos["nome"]
            if "municipio" in sugeridos and not campos["municipio_id"]:
                campos["municipio_id"] = municipioUnico(sugeridos["municipio"], municipios)

        if not campos["nome"]:
            raise _invalido("Informe o nome do atendido ou o atendido existente.")
        if len(campos["nome"]) > 200 or len(campos["telefone"] or "") > 30 or len(campos["email"] or "") > 254:
            raise _invalido("Nome, telefone ou e-mail acima do tamanho permitido.")
        return campos

    @staticmethod
    async def descartar(connection: asyncpg.Connection, usuario: UserInDB, entradaId: uuid.UUID,
                        dados: DescartarRequest) -> Dict[str, Any]:
        tenantId = usuario.tenant_id
        motivo = _limpo(dados.motivo)
        if motivo is None or len(motivo) > MOTIVO_MAXIMO:
            raise _invalido(f"Informe o motivo do descarte, com até {MOTIVO_MAXIMO} caracteres.")
        async with connection.transaction():
            entrada = await BalcaoRepository.obterEntrada(connection, tenantId, entradaId, paraAtualizar=True)
            if entrada is None:
                raise _naoEncontrado("Entrada")
            if entrada["status"] != "PENDENTE":
                raise DomainException("A entrada já foi tratada.", status.HTTP_409_CONFLICT, "Conflito")
            caminhosDescartados = await BalcaoRepository.excluirAnexosDaEntrada(connection, tenantId, entradaId)
            await BalcaoRepository.descartarEntrada(connection, tenantId, entradaId, {
                "motivo": motivo,
                "por_user_id": str(usuario.id),
                "em": datetime.now(timezone.utc).isoformat(),
            })
        BalcaoAnexoService.removerArquivos(caminhosDescartados)
        return {"id": entradaId, "status": "DESCARTADA"}

    @staticmethod
    async def timeline(connection: asyncpg.Connection, tenantId: uuid.UUID,
                       atendidoId: uuid.UUID) -> List[Dict[str, Any]]:
        if await BalcaoRepository.obterAtendido(connection, tenantId, atendidoId) is None:
            raise _naoEncontrado("Atendido")
        eventos = [
            {"tipo": "ATENDIMENTO", "id": a["id"], "protocolo": a["protocolo"], "tipo_evento": a["tipo_evento"],
             "resumo": a["resumo"], "ocorrido_em": a["criado_em"]}
            for a in await BalcaoRepository.listarAtendimentosDoAtendido(connection, tenantId, atendidoId)
        ] + [
            {"tipo": "RESOLUCAO", "id": r["id"], "protocolo": None, "tipo_evento": "RESOLUCAO",
             "resumo": r["despacho"], "ocorrido_em": r["resolvido_em"]}
            for r in await BalcaoRepository.listarResolucoesDoAtendido(connection, tenantId, atendidoId)
        ]
        return sorted(eventos, key=lambda e: e["ocorrido_em"])

    @staticmethod
    async def anexarAoAtendimento(connection: asyncpg.Connection, tenantId: uuid.UUID, atendimentoId: uuid.UUID,
                                  conteudo: bytes) -> Dict[str, Any]:
        if await BalcaoRepository.obterAtendimento(connection, tenantId, atendimentoId) is None:
            raise _naoEncontrado("Atendimento")
        anexo = BalcaoAnexoService.classificar(conteudo)
        return await BalcaoAnexoService.salvar(connection, tenantId, anexo, atendimentoId=atendimentoId)

    @staticmethod
    async def anexoParaDownload(connection: asyncpg.Connection, tenantId: uuid.UUID, anexoId: uuid.UUID):
        return await BalcaoAnexoService.obterParaDownload(connection, tenantId, anexoId)

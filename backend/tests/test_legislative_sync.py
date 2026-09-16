"""Ressincronização manual de um projeto de lei já importado (POST /{id}/sincronizar).

Cobre o contrato do serviço sem tocar rede nem banco: o adaptador da fonte e o
repositório são substituídos por dublês. O que importa aqui é a semântica —
situação atualizada e carimbada, registro preservado quando a fonte falha,
404 para id de outro gabinete.
"""
import uuid
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from app.services import legislative_service as svc
from app.services.legislative_sources import FonteIndisponivelError


TENANT = uuid.uuid4()
PL_ID = uuid.uuid4()


def _registro(situacao="Para Parecer", ementa="Dispõe sobre fisioterapeutas nas maternidades", sync=None):
    return {
        "id_projeto_lei": PL_ID, "tenant_id": TENANT, "fonte": "ALRS",
        "identificador_externo": "bc22b5f7-0132-11f1-bb5d-da08d5ee8534",
        "tipo": "PL", "numero": "5", "ano": 2026, "ementa": ementa,
        "situacao": situacao, "autor": "Delegada Nadine",
        "url_fonte": "https://ww4.al.rs.gov.br/proposicao/PL/5/2026/bc22b5f7",
        "data_apresentacao": None,
        "created_at": datetime(2026, 9, 16, 12, 0, tzinfo=timezone.utc),
        "ultima_sincronizacao": sync,
    }


class _AdaptadorFake:
    def __init__(self, detalhe=None, erro=None):
        self.detalhe, self.erro, self.chamadas = detalhe, erro, []

    async def buscar_detalhe(self, identificador_externo, **kwargs):
        self.chamadas.append((identificador_externo, kwargs))
        if self.erro:
            raise self.erro
        return self.detalhe


@pytest.fixture
def repo(monkeypatch):
    """Repositório em memória: guarda o que o serviço mandou gravar."""
    estado = {"atual": _registro(), "gravado": None}

    async def get(connection, tenantId, projetoLeiId):
        return estado["atual"] if (tenantId, projetoLeiId) == (TENANT, PL_ID) else None

    async def sync(connection, tenantId, projetoLeiId, situacao, ementa=None):
        estado["gravado"] = {"situacao": situacao, "ementa": ementa}
        return _registro(situacao=situacao, ementa=ementa or estado["atual"]["ementa"],
                         sync=datetime.now(timezone.utc))

    monkeypatch.setattr(svc.LegislativeRepository, "getProjetoLeiById", staticmethod(get))
    monkeypatch.setattr(svc.LegislativeRepository, "sincronizarProjetoLei", staticmethod(sync))
    return estado


def _usar_adaptador(monkeypatch, adaptador):
    monkeypatch.setattr(svc, "obter_adaptador", lambda fonte: adaptador)
    return adaptador


async def test_sincronizar_atualiza_situacao_e_sinaliza_mudanca(repo, monkeypatch):
    adaptador = _usar_adaptador(monkeypatch, _AdaptadorFake(
        detalhe={"situacao": "Aprovado em Plenário", "ementa": "Dispõe sobre fisioterapeutas nas maternidades"}
    ))

    resp = await svc.LegislativeService.sincronizarProjetoLei(None, TENANT, PL_ID)

    assert resp.situacao_alterada is True
    assert resp.situacao_anterior == "Para Parecer"
    assert resp.projeto.situacao == "Aprovado em Plenário"
    assert resp.projeto.ultima_sincronizacao is not None
    assert repo["gravado"] == {"situacao": "Aprovado em Plenário",
                               "ementa": "Dispõe sobre fisioterapeutas nas maternidades"}
    # a fonte é consultada com a chave e os metadados guardados, nunca com dado do cliente
    ident, kwargs = adaptador.chamadas[0]
    assert ident == "bc22b5f7-0132-11f1-bb5d-da08d5ee8534"
    assert (kwargs["tipo"], kwargs["numero"], kwargs["ano"]) == ("PL", "5", 2026)


async def test_sincronizar_sem_mudanca_apenas_carimba(repo, monkeypatch):
    _usar_adaptador(monkeypatch, _AdaptadorFake(detalhe={"situacao": "Para Parecer", "ementa": None}))

    resp = await svc.LegislativeService.sincronizarProjetoLei(None, TENANT, PL_ID)

    assert resp.situacao_alterada is False
    assert resp.projeto.situacao == "Para Parecer"
    assert repo["gravado"]["ementa"] is None  # COALESCE no SQL preserva a ementa guardada


async def test_fonte_sem_confirmacao_devolve_502_e_nao_grava(repo, monkeypatch):
    _usar_adaptador(monkeypatch, _AdaptadorFake(detalhe=None))

    with pytest.raises(HTTPException) as exc:
        await svc.LegislativeService.sincronizarProjetoLei(None, TENANT, PL_ID)

    assert exc.value.status_code == 502
    assert repo["gravado"] is None


async def test_fonte_indisponivel_devolve_503_e_nao_grava(repo, monkeypatch):
    _usar_adaptador(monkeypatch, _AdaptadorFake(erro=FonteIndisponivelError("ALRS", TimeoutError())))

    with pytest.raises(HTTPException) as exc:
        await svc.LegislativeService.sincronizarProjetoLei(None, TENANT, PL_ID)

    assert exc.value.status_code == 503
    assert "mantida" in exc.value.detail
    assert repo["gravado"] is None


async def test_id_de_outro_gabinete_devolve_404(repo, monkeypatch):
    adaptador = _usar_adaptador(monkeypatch, _AdaptadorFake(detalhe={"situacao": "x"}))

    with pytest.raises(HTTPException) as exc:
        await svc.LegislativeService.sincronizarProjetoLei(None, uuid.uuid4(), PL_ID)

    assert exc.value.status_code == 404
    assert adaptador.chamadas == []  # não consulta a fonte para id alheio

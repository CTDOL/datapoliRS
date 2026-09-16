"""Adaptadores das fontes oficiais (ALRS, Câmara, Senado) sem tocar a rede —
respx intercepta o httpx. Cobre os três cenários que o usuário enxerga:
resultado, vazio legítimo e fonte fora do ar (que NÃO pode virar "vazio")."""
import httpx
import pytest
import respx

# Testes async rodam via --asyncio-mode=auto (Makefile e CI), sem marker global —
# o marker em teste síncrono parametrizado gera PytestWarning.
from app.services.legislative_sources import (
    AlrsAdapter,
    CamaraAdapter,
    SenadoAdapter,
    FonteIndisponivelError,
    buscar_em_todas_fontes,
    FONTE_ALRS,
    FONTE_CAMARA,
    FONTE_SENADO,
)


ALRS_PESQUISA = "https://ww4.al.rs.gov.br/legislativo/pesquisa"
CAMARA_PROPOSICOES = "https://dadosabertos.camara.leg.br/api/v2/proposicoes"
SENADO_LISTA = "https://legis.senado.leg.br/dadosabertos/senador/lista/atual.json"
SENADO_PROCESSO = "https://legis.senado.leg.br/dadosabertos/processo"

# Recorte fiel da tabela renderizada pelo Drupal da ALRS (capturado em 2026-09-15).
ALRS_HTML_COM_RESULTADO = """
<html><body>
<table class="proposicoes-table">
  <thead><tr><th>Proposição</th><th>Proponente</th><th>Situação</th><th>Tramitação</th><th>Ementa</th></tr></thead>
  <tbody>
    <tr>
      <td><a href="/proposicao/REQ/2/2025/5bd6cb01-2ced-11f0-8ebc-0242ac130005">REQ 2 2025</a></td>
      <td>Deputado(a) Delegada Nadine</td>
      <td>Entrada</td>
      <td>Comis de Constituição e Justiça</td>
      <td class="proposicao-ementa">Reanálise - PLC 288/2024</td>
    </tr>
    <tr>
      <td><a href="/proposicao/PL/288/2024/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee">PL 288 2024</a></td>
      <td>Deputado(a) Delegada Nadine</td>
      <td>Arquivada</td>
      <td>Plenário</td>
      <td class="proposicao-ementa">Institui a Semana Estadual de Prevenção.</td>
    </tr>
  </tbody>
</table>
</body></html>
"""

ALRS_HTML_VAZIO = """
<html><body>
<table class="proposicoes-table">
  <thead><tr><th>Proposição</th><th>Proponente</th><th>Situação</th><th>Tramitação</th><th>Ementa</th></tr></thead>
  <tbody><tr><td colspan="5">Nenhuma proposição encontrada.</td></tr></tbody>
</table>
</body></html>
"""


# --------------------------------------------------------------------------- ALRS

@respx.mock
async def test_alrs_envia_termo_com_curinga_e_extrai_todas_as_colunas():
    rota = respx.get(ALRS_PESQUISA).mock(return_value=httpx.Response(200, text=ALRS_HTML_COM_RESULTADO))

    resultados = await AlrsAdapter().buscar_por_nome("nadine")

    # O portal só casa nome parlamentar completo — sem o curinga, "nadine" nunca acha "Delegada Nadine".
    assert rota.calls.last.request.url.params["nomeProponente"] == "*nadine*"
    assert len(resultados) == 2
    primeira = resultados[0]
    assert primeira.fonte == FONTE_ALRS
    assert primeira.identificador_externo == "5bd6cb01-2ced-11f0-8ebc-0242ac130005"
    assert (primeira.tipo, primeira.numero, primeira.ano) == ("REQ", "2", 2025)
    assert primeira.autor == "Delegada Nadine"  # proponente real, sem o prefixo "Deputado(a)"
    assert primeira.situacao == "Entrada"
    assert primeira.ementa == "Reanálise - PLC 288/2024"
    assert primeira.url_fonte == "https://ww4.al.rs.gov.br/proposicao/REQ/2/2025/5bd6cb01-2ced-11f0-8ebc-0242ac130005"


@pytest.mark.parametrize("entrada, esperado", [
    ("nadine", "*nadine*"),
    ("  Delegada   Nadine ", "*Delegada Nadine*"),
    ("*nadine*", "*nadine*"),
    ("**nadine", "*nadine*"),
])
def test_alrs_normaliza_termo_de_pesquisa(entrada, esperado):
    assert AlrsAdapter._termo_pesquisa(entrada) == esperado


@respx.mock
async def test_alrs_pagina_sem_resultado_retorna_lista_vazia():
    respx.get(ALRS_PESQUISA).mock(return_value=httpx.Response(200, text=ALRS_HTML_VAZIO))

    assert await AlrsAdapter().buscar_por_nome("ninguem") == []


@respx.mock
async def test_alrs_timeout_vira_fonte_indisponivel_e_nao_lista_vazia():
    respx.get(ALRS_PESQUISA).mock(side_effect=httpx.ReadTimeout("lento"))

    with pytest.raises(FonteIndisponivelError) as excinfo:
        await AlrsAdapter().buscar_por_nome("nadine")
    assert excinfo.value.fonte == FONTE_ALRS


@respx.mock
async def test_alrs_http_5xx_vira_fonte_indisponivel():
    respx.get(ALRS_PESQUISA).mock(return_value=httpx.Response(503))

    with pytest.raises(FonteIndisponivelError):
        await AlrsAdapter().buscar_por_nome("nadine")


@respx.mock
async def test_alrs_ignora_linhas_sem_link_de_proposicao():
    html = ALRS_HTML_COM_RESULTADO.replace(
        '<a href="/proposicao/PL/288/2024/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee">PL 288 2024</a>', 'PL 288 2024'
    )
    respx.get(ALRS_PESQUISA).mock(return_value=httpx.Response(200, text=html))

    resultados = await AlrsAdapter().buscar_por_nome("nadine")
    assert [r.identificador_externo for r in resultados] == ["5bd6cb01-2ced-11f0-8ebc-0242ac130005"]


# --------------------------------------------------------------------------- Câmara

@respx.mock
async def test_camara_mapeia_proposicoes():
    respx.get(CAMARA_PROPOSICOES).mock(return_value=httpx.Response(200, json={"dados": [
        {"id": 123, "siglaTipo": "PL", "numero": 10, "ano": 2024, "ementa": "Ementa X", "dataApresentacao": "2024-03-01T10:00"},
    ]}))

    resultados = await CamaraAdapter().buscar_por_nome("fulano")

    assert len(resultados) == 1
    assert resultados[0].fonte == FONTE_CAMARA
    assert resultados[0].identificador_externo == "123"
    assert (resultados[0].tipo, resultados[0].numero, resultados[0].ano) == ("PL", "10", 2024)
    assert str(resultados[0].data_apresentacao) == "2024-03-01"


@respx.mock
async def test_camara_vazia_retorna_lista_vazia():
    respx.get(CAMARA_PROPOSICOES).mock(return_value=httpx.Response(200, json={"dados": []}))
    assert await CamaraAdapter().buscar_por_nome("fulano") == []


@respx.mock
async def test_camara_erro_de_rede_vira_fonte_indisponivel():
    respx.get(CAMARA_PROPOSICOES).mock(side_effect=httpx.ConnectError("down"))
    with pytest.raises(FonteIndisponivelError) as excinfo:
        await CamaraAdapter().buscar_por_nome("fulano")
    assert excinfo.value.fonte == FONTE_CAMARA


@respx.mock
async def test_camara_corpo_nao_json_vira_fonte_indisponivel():
    # Observado em 2026-09-15: gateway da Câmara devolvendo 200 com corpo vazio/HTML.
    respx.get(CAMARA_PROPOSICOES).mock(return_value=httpx.Response(200, text="<html>502</html>"))
    with pytest.raises(FonteIndisponivelError) as excinfo:
        await CamaraAdapter().buscar_por_nome("fulano")
    assert excinfo.value.fonte == FONTE_CAMARA


# --------------------------------------------------------------------------- Senado

def _lista_senadores(*parlamentares):
    return {"ListaParlamentarEmExercicio": {"Parlamentares": {"Parlamentar": list(parlamentares)}}}


def _senador(codigo, nome, uf="RS"):
    return {"IdentificacaoParlamentar": {"CodigoParlamentar": codigo, "NomeParlamentar": nome, "NomeCompletoParlamentar": nome, "UfParlamentar": uf}}


@respx.mock
async def test_senado_resolve_nome_sem_acento_para_codigo_e_busca_materias():
    respx.get(SENADO_LISTA).mock(return_value=httpx.Response(200, json=_lista_senadores(_senador("5", "Mourão"))))
    rota = respx.get(SENADO_PROCESSO).mock(return_value=httpx.Response(200, json=[
        {"id": 77, "identificacao": "PL 91/2023", "ementa": "E", "situacaoAtual": "Em tramitação", "urlDocumento": "u", "dataApresentacao": "2023-05-05"},
    ]))

    resultados = await SenadoAdapter().buscar_por_nome("mourao")

    assert rota.calls.last.request.url.params["codigoParlamentarAutor"] == "5"
    assert len(resultados) == 1
    assert resultados[0].fonte == FONTE_SENADO
    assert (resultados[0].tipo, resultados[0].numero, resultados[0].ano) == ("PL", "91", 2023)


@respx.mock
async def test_senado_ignora_parlamentar_de_outra_uf():
    respx.get(SENADO_LISTA).mock(return_value=httpx.Response(200, json=_lista_senadores(_senador("9", "Nadine", uf="SP"))))
    rota = respx.get(SENADO_PROCESSO)

    assert await SenadoAdapter().buscar_por_nome("nadine") == []
    assert not rota.called


@respx.mock
async def test_senado_erro_de_rede_vira_fonte_indisponivel():
    respx.get(SENADO_LISTA).mock(side_effect=httpx.ReadTimeout("lento"))
    with pytest.raises(FonteIndisponivelError) as excinfo:
        await SenadoAdapter().buscar_por_nome("nadine")
    assert excinfo.value.fonte == FONTE_SENADO


@respx.mock
async def test_senado_detalhe_com_fonte_fora_do_ar_retorna_none():
    respx.get(SENADO_LISTA).mock(side_effect=httpx.ReadTimeout("lento"))
    assert await SenadoAdapter().buscar_detalhe("77", autor="mourao") is None


# --------------------------------------------------------------------------- Agregação

@respx.mock
async def test_agregacao_isola_falha_da_alrs_e_reporta_em_fontes_com_erro():
    respx.get(ALRS_PESQUISA).mock(side_effect=httpx.ReadTimeout("lento"))
    respx.get(CAMARA_PROPOSICOES).mock(return_value=httpx.Response(200, json={"dados": [
        {"id": 1, "siglaTipo": "PL", "numero": 1, "ano": 2024, "ementa": "E"},
    ]}))
    respx.get(SENADO_LISTA).mock(return_value=httpx.Response(200, json=_lista_senadores()))

    resultados, fontes_com_erro = await buscar_em_todas_fontes("nadine")

    assert [r.fonte for r in resultados] == [FONTE_CAMARA]
    assert fontes_com_erro == [FONTE_ALRS]


@respx.mock
async def test_agregacao_todas_ok_sem_fontes_com_erro():
    respx.get(ALRS_PESQUISA).mock(return_value=httpx.Response(200, text=ALRS_HTML_COM_RESULTADO))
    respx.get(CAMARA_PROPOSICOES).mock(return_value=httpx.Response(200, json={"dados": []}))
    respx.get(SENADO_LISTA).mock(return_value=httpx.Response(200, json=_lista_senadores()))

    resultados, fontes_com_erro = await buscar_em_todas_fontes("nadine")

    assert len(resultados) == 2
    assert all(r.fonte == FONTE_ALRS for r in resultados)
    assert fontes_com_erro == []


@respx.mock
async def test_agregacao_erro_inesperado_de_um_adaptador_tambem_vira_fonte_com_erro(monkeypatch):
    from app.services import legislative_sources

    async def explode(self, nome, limite=15):
        raise ValueError("HTML fora do esperado")

    monkeypatch.setattr(legislative_sources.AlrsAdapter, "buscar_por_nome", explode)
    respx.get(CAMARA_PROPOSICOES).mock(return_value=httpx.Response(200, json={"dados": []}))
    respx.get(SENADO_LISTA).mock(return_value=httpx.Response(200, json=_lista_senadores()))

    resultados, fontes_com_erro = await buscar_em_todas_fontes("nadine")

    assert resultados == []
    assert fontes_com_erro == [FONTE_ALRS]

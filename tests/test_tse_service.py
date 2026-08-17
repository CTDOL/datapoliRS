import pytest
import respx
import httpx
from app.services.tse_service import TSEService, TSE_BASE_URL


@pytest.mark.asyncio
@respx.mock
async def test_pesquisar_deputada_rs_sucesso():
    ano = 2026
    codigo_eleicao = "2040402026"
    id_candidato = 12345

    respx.get(f"{TSE_BASE_URL}/listar/{ano}/{codigo_eleicao}/RS/candidatos").mock(
        return_value=httpx.Response(
            200,
            json={
                "candidatos": [
                    {
                        "id": id_candidato,
                        "nomeUrna": "DEPUTADA EXEMPLO",
                        "nomeCompleto": "MARIA DA SILVA EXEMPLO",
                        "cargo": {"codigo": 7, "nome": "Deputado Estadual"}
                    }
                ]
            }
        )
    )

    respx.get(f"{TSE_BASE_URL}/buscar/{ano}/RS/{codigo_eleicao}/candidato/{id_candidato}").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": id_candidato,
                "nomeCompleto": "MARIA DA SILVA EXEMPLO",
                "nomeUrna": "DEPUTADA EXEMPLO",
                "numero": 99123,
                "siglaUf": "RS",
                "partido": {"sigla": "PEX"},
                "cargo": {"nome": "Deputado Estadual"},
                "descricaoSituacao": "DEFERIDO",
                "st_REELEICAO": True,
                "totalDeBens": 150000.0,
                "fotoUrl": "https://exemplo.tse.jus.br/foto.jpg",
                "bens": [
                    {
                        "descricaoDeBem": "Apartamento em Porto Alegre",
                        "dsTipoBemCandidato": "Apartamento",
                        "valor": 150000.0
                    }
                ]
            }
        )
    )

    service = TSEService()
    resultado = await service.pesquisar_deputada_rs("Maria da Silva", ano, codigo_eleicao)

    assert resultado is not None
    assert resultado.id_tse == id_candidato
    assert resultado.nome_urna == "DEPUTADA EXEMPLO"
    assert resultado.reeleicao is True
    assert resultado.total_bens == 150000.0
    assert len(resultado.lista_bens) == 1
    assert resultado.lista_bens[0].valor == 150000.0


@pytest.mark.asyncio
@respx.mock
async def test_pesquisar_deputada_rs_nao_encontrada():
    ano = 2026
    codigo_eleicao = "2040402026"

    respx.get(f"{TSE_BASE_URL}/listar/{ano}/{codigo_eleicao}/RS/candidatos").mock(
        return_value=httpx.Response(200, json={"candidatos": []})
    )

    service = TSEService()
    resultado = await service.pesquisar_deputada_rs("Inexistente", ano, codigo_eleicao)

    assert resultado is None

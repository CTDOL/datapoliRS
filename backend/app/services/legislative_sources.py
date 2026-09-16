import re
import asyncio
import logging
import unicodedata
from typing import List, Optional, Dict, Any, Tuple
import httpx
from bs4 import BeautifulSoup
from app.schemas.legislative import ProposicaoExterna

logger = logging.getLogger("LegislativeSources")

FONTE_ALRS = "ALRS"
FONTE_CAMARA = "CAMARA"
FONTE_SENADO = "SENADO"


class FonteIndisponivelError(Exception):
    """A fonte oficial não respondeu (timeout, 5xx, rede). Distingue "fonte fora
    do ar" de "fonte respondeu e não tem nada" — o segundo é lista vazia, o
    primeiro é este erro, pra que o usuário nunca veja um falso "nenhuma
    proposição encontrada" quando a ALRS simplesmente demorou demais."""

    def __init__(self, fonte: str, causa: Exception):
        self.fonte = fonte
        self.causa = causa
        super().__init__(f"{fonte} indisponível: {type(causa).__name__}: {causa}")


class CamaraAdapter:
    """Câmara dos Deputados — API REST pública, sem autenticação."""

    BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"

    async def buscar_por_nome(self, nome: str, limite: int = 15) -> List[ProposicaoExterna]:
        params = {"autor": nome, "itens": limite, "ordem": "DESC", "ordenarPor": "id"}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.BASE_URL}/proposicoes", params=params)
                response.raise_for_status()
                dados = response.json().get("dados", [])
        except (httpx.HTTPError, ValueError) as erro:
            # ValueError cobre JSONDecodeError: o gateway da Câmara já devolveu 200 com corpo não-JSON.
            logger.error(f"Câmara indisponível ao buscar proposições de '{nome}': {type(erro).__name__}: {erro}")
            raise FonteIndisponivelError(FONTE_CAMARA, erro) from erro

        resultados = []
        for item in dados:
            identificador = str(item.get("id"))
            resultados.append(ProposicaoExterna(
                fonte=FONTE_CAMARA,
                identificador_externo=identificador,
                tipo=item.get("siglaTipo"),
                numero=str(item.get("numero")) if item.get("numero") is not None else None,
                ano=item.get("ano"),
                ementa=item.get("ementa"),
                autor=nome,
                url_fonte=f"https://www.camara.leg.br/proposicoesWeb/fichadetramitacao?idProposicao={identificador}",
                data_apresentacao=_parse_data(item.get("dataApresentacao")),
            ))
        return resultados

    async def buscar_detalhe(self, identificador_externo: str, **_ignored) -> Optional[Dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.BASE_URL}/proposicoes/{identificador_externo}")
                response.raise_for_status()
                item = response.json().get("dados", {})
        except httpx.HTTPError as erro:
            logger.warning(f"Falha ao buscar detalhe da proposição Câmara {identificador_externo}: {erro}")
            return None

        status = item.get("statusProposicao") or {}
        return {
            "tipo": item.get("siglaTipo"),
            "numero": str(item.get("numero")) if item.get("numero") is not None else None,
            "ano": item.get("ano"),
            "ementa": item.get("ementa") or "(ementa não disponível na fonte oficial)",
            "situacao": status.get("descricaoTramitacao"),
            "url_fonte": f"https://www.camara.leg.br/proposicoesWeb/fichadetramitacao?idProposicao={identificador_externo}",
            "data_apresentacao": _parse_data(item.get("dataApresentacao")),
        }


class SenadoAdapter:
    """Senado Federal — API de dados abertos, sem autenticação.

    A busca por matérias exige o código numérico do senador (não o nome), então
    primeiro resolve nome -> código na lista de senadores em exercício pelo RS.
    Usa /dadosabertos/processo (o endpoint /senador/{id}/autorias.json anterior
    está marcado como descontinuado pelo próprio Senado desde 2026-02-01).
    """

    BASE_URL = "https://legis.senado.leg.br/dadosabertos"

    async def _resolver_codigo_senador(self, nome: str, client: httpx.AsyncClient) -> Optional[str]:
        response = await client.get(f"{self.BASE_URL}/senador/lista/atual.json")
        response.raise_for_status()
        parlamentares = (
            response.json()
            .get("ListaParlamentarEmExercicio", {})
            .get("Parlamentares", {})
            .get("Parlamentar", [])
        )
        termo = _sem_acentos(nome)
        for parlamentar in parlamentares:
            identificacao = parlamentar.get("IdentificacaoParlamentar", {})
            if identificacao.get("UfParlamentar") != "RS":
                continue
            nomes = [identificacao.get("NomeParlamentar", ""), identificacao.get("NomeCompletoParlamentar", "")]
            if any(termo in _sem_acentos(n) for n in nomes if n):
                return identificacao.get("CodigoParlamentar")
        return None

    async def buscar_por_nome(self, nome: str, limite: int = 15) -> List[ProposicaoExterna]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                codigo = await self._resolver_codigo_senador(nome, client)
                if not codigo:
                    return []
                response = await client.get(f"{self.BASE_URL}/processo", params={"codigoParlamentarAutor": codigo})
                response.raise_for_status()
                materias = response.json()
        except (httpx.HTTPError, ValueError) as erro:
            logger.error(f"Senado indisponível ao buscar matérias de '{nome}': {type(erro).__name__}: {erro}")
            raise FonteIndisponivelError(FONTE_SENADO, erro) from erro

        if not isinstance(materias, list):
            logger.warning(f"Resposta inesperada do Senado para '{nome}': {materias!r}")
            return []

        resultados = []
        for item in materias[:limite]:
            tipo, numero, ano = _split_identificacao(item.get("identificacao"))
            resultados.append(ProposicaoExterna(
                fonte=FONTE_SENADO,
                identificador_externo=str(item.get("id")),
                tipo=tipo,
                numero=numero,
                ano=ano,
                ementa=item.get("ementa"),
                situacao=item.get("situacaoAtual"),
                autor=nome,
                url_fonte=item.get("urlDocumento"),
                data_apresentacao=_parse_data(item.get("dataApresentacao")),
            ))
        return resultados

    async def buscar_detalhe(self, identificador_externo: str, autor: Optional[str] = None, **_ignored) -> Optional[Dict[str, Any]]:
        if not autor:
            return None
        try:
            encontrados = await self.buscar_por_nome(autor, limite=100)
        except FonteIndisponivelError:
            return None
        for proposicao in encontrados:
            if proposicao.identificador_externo == identificador_externo:
                dados = proposicao.model_dump(exclude={"fonte", "identificador_externo", "ja_importado", "id_projeto_lei"})
                dados["ementa"] = dados.get("ementa") or "(ementa não disponível na fonte oficial)"
                return dados
        return None


class AlrsAdapter:
    """Assembleia Legislativa do RS — sem API pública documentada; a busca de
    proposições e a ficha de cada uma são páginas Drupal renderizadas no
    servidor (sem JS necessário), com estrutura HTML estável — a extração
    abaixo depende dessa estrutura e quebra se o site for redesenhado.

    Colunas da tabela de resultados (medido em 2026-09-15):
    Proposição (link) | Proponente | Situação | Tramitação | Ementa.

    O filtro `nomeProponente` casa o NOME PARLAMENTAR COMPLETO (case-insensitive,
    sem match parcial): "nadine" não encontra "Delegada Nadine". O portal aceita
    curinga `*`, então o termo é enviado como `*nadine*` — mesma semântica de
    "contém" que Câmara e Senado já oferecem.
    """

    BASE_URL = "https://ww4.al.rs.gov.br"
    # A ALRS varia de 0,3s (sem resultado) a 30s+ (consulta "fria"); 10s
    # derrubava a maioria dos acertos. O teto fica abaixo dos 30s do proxy de
    # rewrite do Next.js (proxyTimeout padrão), que cortaria a resposta inteira
    # — incluindo Câmara e Senado — antes de chegar ao navegador.
    TIMEOUT = httpx.Timeout(25.0, connect=10.0)
    _HREF_RE = re.compile(r"/proposicao/([^/]+)/([^/]+)/([^/]+)/([^/?#]+)")
    _PREFIXO_PROPONENTE_RE = re.compile(r"^\s*Deputad[oa]\s*(?:\([oa]\))?\s*", re.IGNORECASE)

    @staticmethod
    def _termo_pesquisa(nome: str) -> str:
        """'  delegada   nadine ' -> '*delegada nadine*'. Curingas digitados pelo
        usuário são removidos pra não gerar '**nadine**'."""
        limpo = " ".join(nome.replace("*", " ").split())
        return f"*{limpo}*"

    async def buscar_por_nome(self, nome: str, limite: int = 15) -> List[ProposicaoExterna]:
        params = {
            "siglaTipoProposicao": "", "nroProposicao": "", "anoProposicao": "",
            "nomeProponente": self._termo_pesquisa(nome), "situacaoProposicao": "",
            "dataIni": "", "dataFim": "",
            "assunto1": "", "assunto2": "", "assunto3": "", "pagina": "1",
        }
        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                response = await client.get(f"{self.BASE_URL}/legislativo/pesquisa", params=params)
                response.raise_for_status()
        except httpx.HTTPError as erro:
            logger.error(f"ALRS indisponível ao buscar proposições de '{nome}': {type(erro).__name__}: {erro}")
            raise FonteIndisponivelError(FONTE_ALRS, erro) from erro

        soup = BeautifulSoup(response.text, "html.parser")
        linhas = soup.select("table.proposicoes-table tbody tr")

        resultados = []
        for linha in linhas[:limite]:
            celulas = linha.find_all("td")
            if len(celulas) < 3:
                continue
            link = celulas[0].find("a")
            if not link or not link.get("href"):
                continue
            match = self._HREF_RE.search(link["href"])
            if not match:
                continue
            tipo, numero, ano, uuid_externo = match.groups()
            proponente = self._PREFIXO_PROPONENTE_RE.sub("", celulas[1].get_text(" ", strip=True))
            situacao = celulas[2].get_text(strip=True)
            ementa = celulas[4].get_text(" ", strip=True) if len(celulas) > 4 else ""
            resultados.append(ProposicaoExterna(
                fonte=FONTE_ALRS,
                identificador_externo=uuid_externo,
                tipo=tipo,
                numero=numero,
                ano=int(ano) if ano.isdigit() else None,
                ementa=ementa or None,
                situacao=situacao or None,
                autor=proponente or nome,
                url_fonte=f"{self.BASE_URL}/proposicao/{tipo}/{numero}/{ano}/{uuid_externo}",
            ))
        return resultados

    async def buscar_detalhe(
        self, identificador_externo: str, tipo: Optional[str] = None,
        numero: Optional[str] = None, ano: Optional[int] = None, **_ignored
    ) -> Optional[Dict[str, Any]]:
        if not (tipo and numero and ano):
            return None
        url = f"{self.BASE_URL}/proposicao/{tipo}/{numero}/{ano}/{identificador_externo}"
        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                response = await client.get(url)
                response.raise_for_status()
        except httpx.HTTPError as erro:
            logger.warning(f"Falha ao buscar detalhe da proposição ALRS {identificador_externo}: {erro}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        ementa_tag = soup.select_one("#content-ementa p")
        ementa = ementa_tag.get_text(strip=True) if ementa_tag else "(ementa não disponível na fonte oficial)"

        situacao = None
        situacao_p = soup.select_one(".proposicao-situacao p")
        if situacao_p:
            rotulo = situacao_p.find("strong")
            rotulo_texto = rotulo.get_text(strip=True) if rotulo else ""
            situacao = situacao_p.get_text(strip=True).replace(rotulo_texto, "", 1).strip() or None

        return {
            "tipo": tipo,
            "numero": numero,
            "ano": ano,
            "ementa": ementa,
            "situacao": situacao,
            "url_fonte": url,
            "data_apresentacao": None,
        }


_ADAPTERS = {
    FONTE_ALRS: AlrsAdapter(),
    FONTE_CAMARA: CamaraAdapter(),
    FONTE_SENADO: SenadoAdapter(),
}


def obter_adaptador(fonte: str):
    adaptador = _ADAPTERS.get(fonte.upper())
    if not adaptador:
        raise ValueError(f"Fonte legislativa desconhecida: {fonte}")
    return adaptador


async def buscar_em_todas_fontes(nome: str) -> Tuple[List[ProposicaoExterna], List[str]]:
    """Consulta ALRS, Câmara e Senado em paralelo. Uma fonte fora do ar não
    derruba as outras: seus resultados entram na lista e a fonte que falhou
    (timeout, 5xx, HTML fora do esperado) volta em `fontes_com_erro`, pra que
    a interface avise "ALRS não respondeu" em vez de um falso "nenhuma
    proposição encontrada"."""
    fontes = list(_ADAPTERS.keys())
    resultados_por_fonte = await asyncio.gather(
        *(_ADAPTERS[fonte].buscar_por_nome(nome) for fonte in fontes),
        return_exceptions=True,
    )
    agregados: List[ProposicaoExterna] = []
    fontes_com_erro: List[str] = []
    for fonte, resultado in zip(fontes, resultados_por_fonte):
        if isinstance(resultado, FonteIndisponivelError):
            fontes_com_erro.append(fonte)
            continue
        if isinstance(resultado, BaseException):
            logger.error(f"Adaptador {fonte} falhou de forma inesperada para '{nome}': {resultado}", exc_info=resultado)
            fontes_com_erro.append(fonte)
            continue
        agregados.extend(resultado)
    return agregados, fontes_com_erro


def _sem_acentos(texto: str) -> str:
    """Normaliza pra comparação de nome sem acento — busca de parlamentar em
    PT-BR precisa aceitar 'Mourao' encontrando 'Mourão'."""
    forma_decomposta = unicodedata.normalize("NFKD", texto.strip().lower())
    return "".join(c for c in forma_decomposta if not unicodedata.combining(c))


def _parse_data(valor: Optional[str]):
    if not valor:
        return None
    try:
        return valor[:10]
    except (TypeError, IndexError):
        return None


def _split_identificacao(identificacao: Optional[str]):
    """'RQS 91/2023' -> ('RQS', '91', 2023)."""
    if not identificacao:
        return None, None, None
    match = re.match(r"^(\S+)\s+(\d+)/(\d+)$", identificacao.strip())
    if not match:
        return None, None, None
    tipo, numero, ano = match.groups()
    return tipo, numero, int(ano)

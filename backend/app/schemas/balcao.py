import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PortalEntradaResposta(BaseModel):
    """Confirmação de recebimento do portal público: sem protocolo e sem id interno."""
    mensagem: str


class PortalCriarRequest(BaseModel):
    rotulo: Optional[str] = Field(default=None, max_length=80)


class PortalCriadoResposta(BaseModel):
    id: uuid.UUID
    rotulo: Optional[str] = None
    token: str
    ativo: bool
    criado_em: datetime


class PortalRevogadoResposta(BaseModel):
    id: uuid.UUID
    ativo: bool


class PortalResumo(BaseModel):
    id: uuid.UUID
    rotulo: Optional[str] = None
    ativo: bool
    criado_em: datetime
    token: Optional[str] = None


class AnexoResumo(BaseModel):
    id: uuid.UUID
    mime_type: str
    tamanho_bytes: int


class SugestaoResponse(BaseModel):
    id: uuid.UUID
    entrada_similar_id: Optional[uuid.UUID] = None
    atendimento_relacionado_id: Optional[uuid.UUID] = None
    score_similaridade: float
    motivo: str


class EntradaResumo(BaseModel):
    id: uuid.UUID
    status: str
    texto_original: str
    dados_extraidos: Dict[str, Any]
    criado_em: datetime


class EntradaDetalhe(EntradaResumo):
    sugestoes: List[SugestaoResponse]
    anexos: List[AnexoResumo]


# Os campos obrigatórios são opcionais no schema de propósito: a falta deles vira 422 RFC 7807
# pelo service, e não o 422 no formato padrão do FastAPI.
class EfetivarRequest(BaseModel):
    atendido_id: Optional[uuid.UUID] = None
    nome: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None
    municipio_id: Optional[str] = None
    resumo: Optional[str] = None
    lideranca_ponto_focal_id: Optional[uuid.UUID] = None
    categoria: Optional[str] = None
    intencao: Optional[str] = None


class EfetivarResponse(BaseModel):
    atendimento_id: uuid.UUID
    atendido_id: uuid.UUID
    protocolo: str


class DescartarRequest(BaseModel):
    motivo: Optional[str] = None


class DescartarResponse(BaseModel):
    id: uuid.UUID
    status: str


class EventoTimeline(BaseModel):
    tipo: str  # ATENDIMENTO ou RESOLUCAO
    id: uuid.UUID
    protocolo: Optional[str] = None
    tipo_evento: Optional[str] = None
    resumo: Optional[str] = None
    ocorrido_em: datetime


class AnexoCriadoResposta(BaseModel):
    id: uuid.UUID
    mime_type: str
    tamanho_bytes: int


class ResolverRequest(BaseModel):
    despacho: Optional[str] = None
    evidencia_anexo_id: Optional[uuid.UUID] = None


class ResolverResponse(BaseModel):
    id: uuid.UUID
    atendimento_id: uuid.UUID
    resolvido_em: datetime


class GrafoNo(BaseModel):
    id: str
    tipo: str  # ATENDIDO, ATENDIMENTO, MUNICIPIO, LIDERANCA ou CATEGORIA
    rotulo: str
    subtitulo: Optional[str] = None


class GrafoAresta(BaseModel):
    origem: str
    destino: str
    tipo: str


class GrafoResposta(BaseModel):
    nos: List[GrafoNo]
    arestas: List[GrafoAresta]


class MotorAtivoResposta(BaseModel):
    provider: str
    model: str = ""


class LiderancaSugeridaItem(BaseModel):
    id_lideranca: uuid.UUID
    nm_completo: str
    ds_cargo: Optional[str] = None
    vinculada_municipio: bool = False


class LiderancasSugeridasResposta(BaseModel):
    no_municipio: List[LiderancaSugeridaItem]
    outras_do_gabinete: List[LiderancaSugeridaItem]


class CategoriaResumo(BaseModel):
    id: uuid.UUID
    nome: str
    slug: str
    uso_count: int = 1


class PontoFocalAtualizarRequest(BaseModel):
    lideranca_ponto_focal_id: Optional[uuid.UUID] = None


class PontoFocalAtualizarResposta(BaseModel):
    atendimento_id: uuid.UUID
    lideranca_ponto_focal_id: Optional[uuid.UUID] = None
    lideranca_nome: Optional[str] = None


class IaConfigResposta(BaseModel):
    provider: str
    model: str = ""
    base_url: str = ""
    api_key_configurada: bool
    provedores_suportados: List[str]


class IaConfigAtualizarRequest(BaseModel):
    provider: str
    model: str = ""
    base_url: str = ""
    api_key: Optional[str] = None
    limpar_api_key: bool = False


class IaConfigTestarRequest(BaseModel):
    provider: Optional[str] = None
    model: str = ""
    base_url: str = ""
    api_key: Optional[str] = None


class IaConfigTesteResposta(BaseModel):
    ok: bool
    provider: str
    model: str = ""
    latencia_ms: int = 0
    detalhe: str
    resultado: Dict[str, str] = {}


class PedidoMapaItem(BaseModel):
    id: uuid.UUID
    tipo: str
    resumo: str
    nome_atendido: Optional[str] = None
    municipio_id: str
    municipio_nome: str
    latitude: float
    longitude: float
    criado_em: datetime

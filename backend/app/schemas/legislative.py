from typing import Optional
from uuid import UUID
from datetime import date, datetime
from pydantic import BaseModel, Field, ConfigDict


class ProposicaoExterna(BaseModel):
    """Resultado de busca numa fonte oficial — ainda não persistido no gabinete."""
    fonte: str = Field(..., description="ALRS, CAMARA ou SENADO")
    identificador_externo: str = Field(..., description="Chave estável na fonte, usada pra evitar importar duplicado")
    tipo: Optional[str] = None
    numero: Optional[str] = None
    ano: Optional[int] = None
    ementa: Optional[str] = None
    situacao: Optional[str] = None
    autor: Optional[str] = None
    url_fonte: Optional[str] = None
    data_apresentacao: Optional[date] = None
    ja_importado: bool = False
    id_projeto_lei: Optional[UUID] = None


class BuscaExternaResponse(BaseModel):
    """Resultado agregado de ALRS + Câmara + Senado. `fontes_com_erro` lista as
    fontes que não responderam (timeout/5xx) nesta consulta — lista vazia de
    resultados só significa "nada encontrado" quando `fontes_com_erro` também
    está vazia."""
    resultados: list[ProposicaoExterna]
    fontes_com_erro: list[str] = Field(default_factory=list, description="Ex.: ['ALRS'] quando a Assembleia deu timeout")


class ProjetoLeiImport(BaseModel):
    """Só identifica QUAL proposição importar — ementa/situação/url são

    revalidadas direto na fonte oficial no momento da importação (o backend
    não confia em texto de ementa vindo do cliente, já que a promessa do
    recurso é 'dado oficial').
    """
    fonte: str = Field(..., max_length=20)
    identificador_externo: str = Field(..., max_length=120)
    tipo: Optional[str] = Field(None, max_length=20)
    numero: Optional[str] = Field(None, max_length=20)
    ano: Optional[int] = None
    autor: Optional[str] = Field(None, max_length=255)


class ProjetoLeiResponse(BaseModel):
    id_projeto_lei: UUID
    tenant_id: UUID
    fonte: str
    identificador_externo: str
    tipo: Optional[str] = None
    numero: Optional[str] = None
    ano: Optional[int] = None
    ementa: str
    situacao: Optional[str] = None
    autor: Optional[str] = None
    url_fonte: Optional[str] = None
    data_apresentacao: Optional[date] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjetoLeiPageResponse(BaseModel):
    items: list[ProjetoLeiResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ObservadorAdd(BaseModel):
    id_lideranca: UUID


class ObservadorResponse(BaseModel):
    id_lideranca: UUID
    nm_completo: str

    model_config = ConfigDict(from_attributes=True)

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class MunicipioAtuacao(BaseModel):
    """Um município de atuação de uma liderança, já com o centróide geográfico
    resolvido — usado para plotar um marcador por município no mapa tático."""
    cd_ibge_7: str
    nm_municipio: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class LiderancaBase(BaseModel):
    nm_completo: str = Field(..., min_length=3, max_length=255, description="Nome completo da liderança/apoiador")
    nr_telefone: Optional[str] = Field(None, max_length=30, description="Telefone / WhatsApp de contato")
    ds_email: Optional[str] = Field(None, max_length=255, description="E-mail de contato")
    tp_influencia: Optional[str] = Field(None, max_length=50, description="Categoria de influência (ex: Comunitária, Religiosa, Sindical)")
    ds_observacoes: Optional[str] = Field(None, description="Anotações e histórico de demandas políticas")
    is_ativo: bool = Field(default=True, description="Status de atividade da liderança")


class LiderancaCreate(LiderancaBase):
    municipios: List[str] = Field(..., min_length=1, description="Códigos IBGE dos municípios de atuação (pelo menos 1)")


class LiderancaUpdate(BaseModel):
    nm_completo: Optional[str] = Field(None, min_length=3, max_length=255)
    nr_telefone: Optional[str] = None
    ds_email: Optional[str] = None
    tp_influencia: Optional[str] = None
    ds_observacoes: Optional[str] = None
    is_ativo: Optional[bool] = None
    municipios: Optional[List[str]] = Field(None, min_length=1, description="Quando informado, substitui a lista inteira de municípios de atuação")


class LiderancaResponse(LiderancaBase):
    id_lideranca: UUID
    tenant_id: UUID
    ds_foto_url: Optional[str] = None
    municipios: List[MunicipioAtuacao] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LiderancaPageResponse(BaseModel):
    items: list[LiderancaResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

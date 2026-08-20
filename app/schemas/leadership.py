from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class LiderancaBase(BaseModel):
    cd_ibge_7: Optional[str] = Field(None, description="Código IBGE do município de atuação")
    nm_completo: str = Field(..., min_length=3, max_length=255, description="Nome completo da liderança/apoiador")
    nr_telefone: Optional[str] = Field(None, max_length=30, description="Telefone / WhatsApp de contato")
    ds_email: Optional[str] = Field(None, max_length=255, description="E-mail de contato")
    tp_influencia: Optional[str] = Field(None, max_length=50, description="Categoria de influência (ex: Comunitária, Religiosa, Sindical)")
    ds_observacoes: Optional[str] = Field(None, description="Anotações e histórico de demandas políticas")
    is_ativo: bool = Field(default=True, description="Status de atividade da liderança")


class LiderancaCreate(LiderancaBase):
    pass


class LiderancaUpdate(BaseModel):
    cd_ibge_7: Optional[str] = None
    nm_completo: Optional[str] = Field(None, min_length=3, max_length=255)
    nr_telefone: Optional[str] = None
    ds_email: Optional[str] = None
    tp_influencia: Optional[str] = None
    ds_observacoes: Optional[str] = None
    is_ativo: Optional[bool] = None


from pydantic import BaseModel, Field, ConfigDict

class LiderancaResponse(LiderancaBase):
    id_lideranca: UUID
    tenant_id: UUID
    nm_municipio: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

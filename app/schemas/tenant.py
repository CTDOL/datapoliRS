from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class TenantProfileResponse(BaseModel):
    id_tenant: UUID
    nm_mandato: str
    ds_cargo_mandato: str
    cd_cargo: Optional[int] = None
    ds_cargo: Optional[str] = None
    nr_partido: Optional[int] = None
    sg_partido: Optional[str] = None
    cd_ibge_base: Optional[str] = None
    nm_municipio_base: Optional[str] = None
    is_ativo: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TenantProfileUpdate(BaseModel):
    nm_mandato: Optional[str] = Field(None, min_length=3, max_length=150)
    cd_cargo: Optional[int] = None
    nr_partido: Optional[int] = None
    cd_ibge_base: Optional[str] = None

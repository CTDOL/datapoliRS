from typing import Optional
from pydantic import BaseModel, Field


class GabineteCreate(BaseModel):
    nm_mandato: str = Field(..., min_length=3, max_length=200)
    ds_cargo_mandato: str = Field(..., min_length=3, max_length=100)
    cd_ibge_base: Optional[str] = Field(None, min_length=7, max_length=7)
    email_admin: str = Field(..., min_length=5, max_length=200)
    senha_inicial: str = Field(..., min_length=8, max_length=200)


class GabineteStatusUpdate(BaseModel):
    is_ativo: bool


class SenhaAdminUpdate(BaseModel):
    email_admin: str = Field(..., min_length=5, max_length=200)
    senha_nova: str = Field(..., min_length=8, max_length=200)


class GabineteResumo(BaseModel):
    id_tenant: str
    nm_mandato: str
    ds_cargo_mandato: str
    is_ativo: bool
    emails_admin: Optional[str] = None

from typing import List, Optional
from pydantic import BaseModel, Field


class ApiFonteResponse(BaseModel):
    fonte: str
    nome: str
    base_url: str
    ativa: bool
    padrao: str = Field(description="Endereço original da integração, para o operador comparar")


class MaxMindStatus(BaseModel):
    base_local_encontrada: bool
    observacao: str


class ApisResponse(BaseModel):
    fontes: List[ApiFonteResponse]
    maxmind: MaxMindStatus


class ApiFonteUpdate(BaseModel):
    fonte: str = Field(pattern="^(tse|camara|senado|alrs)$")
    base_url: str = Field(min_length=8, max_length=255)
    ativa: bool


class ApisUpdateRequest(BaseModel):
    fontes: List[ApiFonteUpdate]
    motivo: Optional[str] = Field(default=None, max_length=255)

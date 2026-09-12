from typing import Dict
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ConfiguracaoItem(BaseModel):
    chave: str
    valor: str
    tipo: str
    categoria: str
    descricao: str
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConfiguracoesUpdateRequest(BaseModel):
    valores: Dict[str, str]

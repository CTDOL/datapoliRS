from typing import Optional
from uuid import UUID
from datetime import date, datetime
from pydantic import BaseModel, Field, ConfigDict

TAREFA_STATUS_VALIDOS = ("Pendente", "Em Andamento", "Concluída")


class TarefaCreate(BaseModel):
    id_projeto_lei: Optional[UUID] = None
    id_emenda: Optional[UUID] = None
    id_lideranca_responsavel: Optional[UUID] = None
    titulo: str = Field(..., min_length=3, max_length=255)
    descricao: Optional[str] = None
    prazo: Optional[date] = None
    tp_status: str = Field(default="Pendente", max_length=20)


class TarefaUpdate(BaseModel):
    id_lideranca_responsavel: Optional[UUID] = None
    titulo: Optional[str] = Field(None, min_length=3, max_length=255)
    descricao: Optional[str] = None
    prazo: Optional[date] = None
    tp_status: Optional[str] = None


class TarefaResponse(BaseModel):
    id_tarefa: UUID
    tenant_id: UUID
    id_projeto_lei: Optional[UUID] = None
    id_emenda: Optional[UUID] = None
    id_lideranca_responsavel: Optional[UUID] = None
    nm_lideranca_responsavel: Optional[str] = None
    titulo: str
    descricao: Optional[str] = None
    prazo: Optional[date] = None
    tp_status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

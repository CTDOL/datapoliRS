from typing import List, Literal, Optional, get_args
from uuid import UUID
from datetime import date, datetime
from pydantic import BaseModel, Field, ConfigDict

# Status gravados (ADR 046 §2.3). O banco tem o mesmo domínio num CHECK (migração r8b9c0d1e2f3).
StatusTarefa = Literal["Pendente", "Em Andamento", "Concluída", "Cancelada"]
TAREFA_STATUS_VALIDOS = get_args(StatusTarefa)


class TarefaCreate(BaseModel):
    id_projeto_lei: Optional[UUID] = None
    id_emenda: Optional[UUID] = None
    # Campo legado (um responsável). Mantido para clientes antigos; use ids_responsaveis nos novos.
    id_lideranca_responsavel: Optional[UUID] = None
    ids_responsaveis: Optional[List[UUID]] = None
    titulo: str = Field(..., min_length=3, max_length=255)
    descricao: Optional[str] = None
    prazo: Optional[date] = None
    tp_status: StatusTarefa = "Pendente"


class TarefaUpdate(BaseModel):
    id_lideranca_responsavel: Optional[UUID] = None
    ids_responsaveis: Optional[List[UUID]] = None
    titulo: Optional[str] = Field(None, min_length=3, max_length=255)
    descricao: Optional[str] = None
    prazo: Optional[date] = None
    tp_status: Optional[StatusTarefa] = None


class ResponsavelTarefa(BaseModel):
    id_lideranca: UUID
    nm_completo: str
    ds_foto_url: Optional[str] = None


class TarefaResponse(BaseModel):
    id_tarefa: UUID
    tenant_id: UUID
    id_projeto_lei: Optional[UUID] = None
    id_emenda: Optional[UUID] = None
    id_lideranca_responsavel: Optional[UUID] = None
    nm_lideranca_responsavel: Optional[str] = None
    ds_foto_url_responsavel: Optional[str] = None
    responsaveis: List[ResponsavelTarefa] = Field(default_factory=list)
    titulo: str
    descricao: Optional[str] = None
    prazo: Optional[date] = None
    tp_status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

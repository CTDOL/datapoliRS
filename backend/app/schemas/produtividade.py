from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class ComentarioCreate(BaseModel):
    texto: str = Field(..., min_length=1, max_length=2000)

    @field_validator("texto")
    @classmethod
    def _sem_espacos_apenas(cls, valor: str) -> str:
        limpo = valor.strip()
        if not limpo:
            raise ValueError("O comentário não pode ser vazio.")
        return limpo


class ComentarioResponse(BaseModel):
    id_comentario: UUID
    id_tarefa: UUID
    autor_email: str
    texto: str
    created_at: datetime


class TotaisTarefas(BaseModel):
    total: int
    pendente: int
    em_andamento: int
    concluida: int
    atrasadas: int


class CargaResponsavel(BaseModel):
    nome: Optional[str]
    abertas: int
    concluidas: int


class ProdutividadeResponse(BaseModel):
    tarefas: TotaisTarefas
    por_responsavel: List[CargaResponsavel]
    comentarios_ultimos_7_dias: int
    projetos_lei: int
    emendas: int

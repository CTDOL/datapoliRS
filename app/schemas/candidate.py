from typing import List, Optional
from pydantic import BaseModel, Field


class BemDeclarado(BaseModel):
    descricao: Optional[str] = None
    tipo: Optional[str] = None
    valor: float = Field(default=0.0)


class CandidataDetalhada(BaseModel):
    id_tse: int
    nome_completo: str
    nome_urna: str
    numero_urna: int
    sigla_uf: str = "RS"
    partido: str
    cargo: str
    situacao_candidatura: Optional[str] = None
    reeleicao: bool = False
    total_bens: float = Field(default=0.0)
    lista_bens: List[BemDeclarado] = []
    foto_url: Optional[str] = None

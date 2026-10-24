from typing import Literal, Optional
from pydantic import BaseModel

TipoTema = Literal["escuro", "claro"]


class TemaUpdate(BaseModel):
    cor_primaria: Optional[str] = None
    cor_secundaria: Optional[str] = None
    # None mantém o tema atual: salvar só as cores não muda claro/escuro.
    tp_tema: Optional[TipoTema] = None


class TemaResponse(BaseModel):
    cor_primaria: Optional[str] = None
    cor_secundaria: Optional[str] = None
    tp_tema: TipoTema = "escuro"

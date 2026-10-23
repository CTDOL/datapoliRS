from typing import Optional
from pydantic import BaseModel


class TemaUpdate(BaseModel):
    cor_primaria: Optional[str] = None
    cor_secundaria: Optional[str] = None


class TemaResponse(BaseModel):
    cor_primaria: Optional[str] = None
    cor_secundaria: Optional[str] = None

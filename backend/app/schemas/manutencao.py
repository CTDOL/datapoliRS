from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class SaudePleito(BaseModel):
    cd_eleicao: str
    ano_eleicao: int
    ds_eleicao: str
    nr_turno: int
    linhas_votacao: int
    municipios_votacao: int
    zonas_votacao: int
    codigos_sem_cadastro: int
    linhas_comparecimento: int


class CargaEtl(BaseModel):
    id_carga: int
    tipo: str
    ano_eleicao: int
    cd_eleicoes: List[str]
    arquivo_origem: str
    sha256: str
    tamanho_bytes: int
    iniciado_em: datetime
    concluido_em: datetime
    status: str
    linhas_carregadas: Optional[int] = None
    erro: Optional[str] = None
    operador: str


class JobEtlCreate(BaseModel):
    tipo: Literal["votacao", "comparecimento"]
    ano: int = Field(..., ge=2000, le=2100)
    confirmacao: str = Field(..., max_length=100)


class JobEtl(BaseModel):
    id_job: int
    tipo: str
    ano_eleicao: int
    status: str
    solicitado_por: str
    solicitado_em: datetime
    iniciado_em: Optional[datetime] = None
    concluido_em: Optional[datetime] = None
    erro: Optional[str] = None


class AtivarPleitoRequest(BaseModel):
    cd_eleicao: str = Field(..., min_length=1, max_length=20)
    confirmacao: str = Field(..., max_length=50)
    aceitar_codigos_sem_cadastro: bool = False


class PleitoAtivo(BaseModel):
    cd_eleicao: str
    ano_eleicao: int
    anterior_cd_eleicao: str
    anterior_ano_eleicao: int

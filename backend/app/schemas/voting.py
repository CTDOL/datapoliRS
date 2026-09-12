from typing import List, Optional
from pydantic import BaseModel, Field


class CandidatoBuscaItem(BaseModel):
    sq_candidato: int
    nr_candidato: int
    nm_urna_candidato: str
    nm_candidato: str
    cd_cargo: int
    ds_cargo: str
    sg_partido: str
    sg_uf: str = "RS"
    foto_url: Optional[str] = None
    ds_situacao_candidatura: Optional[str] = None


class MunicipioVotacaoItem(BaseModel):
    cd_tse_municipio: str
    nm_municipio: str
    cd_ibge_7: Optional[str] = None
    votos: int = Field(..., description="Quantidade total de votos nominais recebidos no município")
    percentual_total_candidato: float = Field(default=0.0, description="Percentual dos votos do candidato concentrados neste município")


class VotacaoCandidatoResponse(BaseModel):
    sq_candidato: int
    nr_candidato: int
    nm_urna_candidato: str
    nm_candidato: str
    ds_cargo: str
    sg_partido: str
    cd_eleicao: str
    total_votos_estado: int
    municipios_votados: int
    distribuicao_municipios: List[MunicipioVotacaoItem]

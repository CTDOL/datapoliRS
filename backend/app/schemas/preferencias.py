from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict

MapaPadrao = Literal["liderancas", "votacao", "cruzada"]


class FontesPreferidas(BaseModel):
    """Fontes legislativas que o usuário quer consultar na busca externa de projetos de lei."""
    model_config = ConfigDict(extra="forbid")

    alrs: bool = True
    camara: bool = True
    senado: bool = True


class PreferenciasUsuario(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mapa_padrao: MapaPadrao = "liderancas"
    fontes_legislativas: FontesPreferidas = FontesPreferidas()


class PreferenciasUsuarioUpdate(BaseModel):
    """Atualização parcial: só o que vier preenchido é gravado."""
    model_config = ConfigDict(extra="forbid")

    mapa_padrao: Optional[MapaPadrao] = None
    fontes_legislativas: Optional[FontesPreferidas] = None

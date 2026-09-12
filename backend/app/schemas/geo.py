from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class MunicipioGeoProperty(BaseModel):
    id: str = Field(..., description="Código IBGE de 7 dígitos")
    name: str = Field(..., description="Nome do Município")
    cd_tse: Optional[str] = Field(None, description="Código do TSE de 5 dígitos")
    description: Optional[str] = None


class GeoJsonFeature(BaseModel):
    type: str = "Feature"
    properties: MunicipioGeoProperty
    geometry: Dict[str, Any]


class GeoJsonFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: List[GeoJsonFeature]

from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


class EmendaBase(BaseModel):
    cd_ibge_7: Optional[str] = Field(None, description="Código IBGE do município beneficiário")
    nr_emenda: Optional[str] = Field(None, max_length=50, description="Número oficial da emenda")
    ano_exercicio: int = Field(..., ge=2000, le=2100, description="Ano orçamentário de exercício")
    tp_emenda: Optional[str] = Field(None, max_length=30, description="Tipo: Individual, Bancada, Comissão, Relator")
    ds_area: Optional[str] = Field(None, max_length=100, description="Área temática (Saúde, Educação, Infraestrutura...)")
    ds_objeto: str = Field(..., min_length=3, description="Finalidade/objeto da emenda")
    vl_indicado: Decimal = Field(default=Decimal("0"), ge=0, description="Valor indicado")
    vl_empenhado: Decimal = Field(default=Decimal("0"), ge=0, description="Valor empenhado")
    vl_pago: Decimal = Field(default=Decimal("0"), ge=0, description="Valor pago")
    tp_situacao: str = Field(default="Indicada", max_length=30, description="Situação: Indicada, Empenhada, Paga, Cancelada")
    ds_observacoes: Optional[str] = None


class EmendaCreate(EmendaBase):
    pass


class EmendaUpdate(BaseModel):
    cd_ibge_7: Optional[str] = None
    nr_emenda: Optional[str] = None
    ano_exercicio: Optional[int] = Field(None, ge=2000, le=2100)
    tp_emenda: Optional[str] = None
    ds_area: Optional[str] = None
    ds_objeto: Optional[str] = Field(None, min_length=3)
    vl_indicado: Optional[Decimal] = Field(None, ge=0)
    vl_empenhado: Optional[Decimal] = Field(None, ge=0)
    vl_pago: Optional[Decimal] = Field(None, ge=0)
    tp_situacao: Optional[str] = None
    ds_observacoes: Optional[str] = None


class EmendaResponse(EmendaBase):
    id_emenda: UUID
    tenant_id: UUID
    nm_municipio: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EmendaPageResponse(BaseModel):
    items: list[EmendaResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class EmendaKpis(BaseModel):
    total_emendas: int
    vl_total_indicado: Decimal
    vl_total_empenhado: Decimal
    vl_total_pago: Decimal
    por_situacao: dict[str, int]

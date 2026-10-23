"""Cores do gabinete (ADR 038).

A cor primária é o fundo dos botões e do item ativo da navegação, e o texto sobre ela é branco.
Por isso ela precisa de contraste mínimo WCAG AA (4.5:1) contra o branco.
"""
import re
from typing import Optional

import asyncpg
from fastapi import HTTPException, status

from app.schemas.tema import TemaUpdate

PADRAO_HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
CONTRASTE_MINIMO = 4.5


def _luminancia(hexa: str) -> float:
    """Luminância relativa (WCAG 2.x) de uma cor #RRGGBB."""
    canais = []
    for i in (1, 3, 5):
        c = int(hexa[i:i + 2], 16) / 255
        canais.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    r, g, b = canais
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contraste_com_branco(hexa: str) -> float:
    return 1.05 / (_luminancia(hexa) + 0.05)


def validar_cor_primaria(hexa: Optional[str]) -> None:
    if hexa is None:
        return
    if not PADRAO_HEX.match(hexa):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="Cor em formato inválido. Use #RRGGBB.")
    razao = contraste_com_branco(hexa)
    if razao < CONTRASTE_MINIMO:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Cor com contraste insuficiente para o texto branco ({razao:.2f}:1; mínimo 4.5:1).",
        )


async def obter_tema(connection: asyncpg.Connection, id_tenant) -> dict:
    linha = await connection.fetchrow(
        "SELECT cor_primaria, cor_secundaria FROM tb_tenants WHERE id_tenant = $1", id_tenant
    )
    return {"cor_primaria": linha["cor_primaria"], "cor_secundaria": linha["cor_secundaria"]} if linha else \
        {"cor_primaria": None, "cor_secundaria": None}


async def salvar_tema(connection: asyncpg.Connection, id_tenant, payload: TemaUpdate) -> dict:
    validar_cor_primaria(payload.cor_primaria)
    if payload.cor_secundaria is not None and not PADRAO_HEX.match(payload.cor_secundaria):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="Cor secundária em formato inválido. Use #RRGGBB.")
    await connection.execute(
        "UPDATE tb_tenants SET cor_primaria = $2, cor_secundaria = $3 WHERE id_tenant = $1",
        id_tenant, payload.cor_primaria, payload.cor_secundaria,
    )
    return {"cor_primaria": payload.cor_primaria, "cor_secundaria": payload.cor_secundaria}

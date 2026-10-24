"""O log da conexão com o banco não pode conter a senha (revisão de 2026-10-24, achado M1)."""
import asyncio
import logging
from app.core import database
from app.core.config import settings

SENHA = "senha-que-nao-pode-vazar"


def test_log_do_pool_nao_contem_a_senha(monkeypatch, caplog):
    async def poolFalso(**kwargs):
        return object()

    monkeypatch.setattr(settings, "DATABASE_URL", f"postgresql://usuario:{SENHA}@banco:5432/datapoli")
    monkeypatch.setattr(database, "databasePool", None)
    monkeypatch.setattr(database.asyncpg, "create_pool", poolFalso)

    with caplog.at_level(logging.INFO, logger="DatabasePool"):
        asyncio.run(database.initializeDatabasePool())

    assert caplog.records, "o pool deveria registrar a conexão"
    assert SENHA not in caplog.text
    assert "banco" in caplog.text  # o host continua no log, para diagnóstico

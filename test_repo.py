import asyncio
from app.database import database
from app.repositories.cabinet_repository import CabinetRepository

async def test_repo():
    print("Connecting to DB...")
    await database.connect()
    print("Connected.")
    print("Fetching liderancas...")
    # we need a fake tenant id? The repository might not need tenant_id if we bypass it, or we just fetch raw SQL.
    query = """
        SELECT 
            l.id_lideranca,
            l.nm_completo,
            l.cd_ibge_7,
            l.tp_influencia,
            l.is_ativo,
            l.tenant_id,
            l.created_at,
            m.nm_municipio,
            ST_Y(ST_Centroid(m.geometria)) as latitude,
            ST_X(ST_Centroid(m.geometria)) as longitude
        FROM tb_gabinete_liderancas l
        LEFT JOIN tb_municipios m ON l.cd_ibge_7 = m.cd_ibge_7
    """
    results = await database.fetch_all(query=query)
    for r in results:
        print(dict(r))
    
    await database.disconnect()

if __name__ == "__main__":
    asyncio.run(test_repo())

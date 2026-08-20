# Matriz RACI — datapoliRS

## Papéis considerados

- **BE**: Engenharia Backend/API  
- **DE**: Engenharia de Dados/ETL  
- **FE**: Engenharia Frontend  
- **DEVOPS**: Infraestrutura e Operações  
- **PO**: Product Owner / Gestão Funcional

> Legenda: **R** (Responsible), **A** (Accountable), **C** (Consulted), **I** (Informed)

## RACI por área e arquivo

| Área | Arquivo | R | A | C | I |
|---|---|---|---|---|---|
| API/App | `/home/runner/work/datapoliRS/datapoliRS/app/main.py` | BE | BE | DEVOPS | PO |
| Configuração | `/home/runner/work/datapoliRS/datapoliRS/app/core/config.py` | BE | BE | DEVOPS | PO |
| Banco/Pool | `/home/runner/work/datapoliRS/datapoliRS/app/core/database.py` | BE | BE | DEVOPS, DE | PO |
| Cache/Redis | `/home/runner/work/datapoliRS/datapoliRS/app/core/redis_client.py` | BE | BE | DEVOPS | PO |
| Dependências/Auth Context | `/home/runner/work/datapoliRS/datapoliRS/app/core/dependencies.py` | BE | BE | DEVOPS | PO |
| Exceções Globais | `/home/runner/work/datapoliRS/datapoliRS/app/core/exceptions.py` | BE | BE | DEVOPS | PO |
| Rotas de Votação | `/home/runner/work/datapoliRS/datapoliRS/app/routers/voting.py` | BE | BE | FE, DE | PO |
| Rotas Geo | `/home/runner/work/datapoliRS/datapoliRS/app/routers/geo.py` | BE | BE | FE, DE | PO |
| Rotas Gabinete | `/home/runner/work/datapoliRS/datapoliRS/app/routers/cabinet.py` | BE | BE | PO | FE |
| Rotas Auth | `/home/runner/work/datapoliRS/datapoliRS/app/routers/auth.py` | BE | BE | DEVOPS | PO |
| Serviço TSE | `/home/runner/work/datapoliRS/datapoliRS/app/services/tse_service.py` | BE | BE | DE | PO |
| Serviço Votação | `/home/runner/work/datapoliRS/datapoliRS/app/services/voting_service.py` | BE | BE | DE, FE | PO |
| Serviço Geo | `/home/runner/work/datapoliRS/datapoliRS/app/services/geo_service.py` | BE | BE | DE, FE | PO |
| Serviço Gabinete | `/home/runner/work/datapoliRS/datapoliRS/app/services/cabinet_service.py` | BE | BE | PO | FE |
| Serviço Auth | `/home/runner/work/datapoliRS/datapoliRS/app/services/auth_service.py` | BE | BE | DEVOPS | PO |
| Repo Candidatos | `/home/runner/work/datapoliRS/datapoliRS/app/repositories/candidate_repository.py` | BE | BE | DE | PO |
| Repo Votação | `/home/runner/work/datapoliRS/datapoliRS/app/repositories/voting_repository.py` | BE | BE | DE | PO |
| Repo Geo | `/home/runner/work/datapoliRS/datapoliRS/app/repositories/geo_repository.py` | BE | BE | DE | PO |
| Repo Gabinete | `/home/runner/work/datapoliRS/datapoliRS/app/repositories/cabinet_repository.py` | BE | BE | PO | FE |
| Schemas API | `/home/runner/work/datapoliRS/datapoliRS/app/schemas/*.py` | BE | BE | FE, DE | PO |
| Frontend HTML | `/home/runner/work/datapoliRS/datapoliRS/app/static/index.html` | FE | FE | BE | PO |
| Frontend JS | `/home/runner/work/datapoliRS/datapoliRS/app/static/script.js` | FE | FE | BE | PO |
| Frontend CSS | `/home/runner/work/datapoliRS/datapoliRS/app/static/style.css` | FE | FE | BE | PO |
| GeoJSON Fallback | `/home/runner/work/datapoliRS/datapoliRS/app/static/rs_municipios.json` | DE | DE | FE, BE | PO |
| ETL TSE | `/home/runner/work/datapoliRS/datapoliRS/etl/ingest_tse.py` | DE | DE | BE, DEVOPS | PO |
| ETL Geo Municípios | `/home/runner/work/datapoliRS/datapoliRS/etl/import_municipios_geojson.py` | DE | DE | BE, DEVOPS | PO |
| Script Processamento | `/home/runner/work/datapoliRS/datapoliRS/scripts/processar_votos.py` | DE | DE | BE | PO |
| Testes API/Serviços | `/home/runner/work/datapoliRS/datapoliRS/tests/*.py` | BE | BE | DE, FE | PO |

## Observações

- Esta matriz é uma referência operacional para coordenação entre equipes.
- Em mudanças de segurança, autenticação e deploy, recomenda-se elevar **DEVOPS** para **C** obrigatório na revisão.
- Caso a governança do projeto use papéis nominais, substitua as siglas por pessoas/equipes oficiais.

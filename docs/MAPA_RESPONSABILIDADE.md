# Mapa de Responsabilidade por Arquivo — datapoliRS

Este documento descreve a responsabilidade principal dos arquivos-chave do repositório.

## Backend — Orquestração e Infra

- `/home/runner/work/datapoliRS/datapoliRS/app/main.py`  
  Ponto de entrada da API FastAPI; configura ciclo de vida, CORS, handlers globais, rotas e endpoints legados.

- `/home/runner/work/datapoliRS/datapoliRS/app/core/config.py`  
  Centraliza configurações da aplicação via Pydantic Settings (API, banco, Redis, autenticação e TSE).

- `/home/runner/work/datapoliRS/datapoliRS/app/core/database.py`  
  Gerencia pool assíncrono do PostgreSQL (`asyncpg`) e provê conexões para uso nas dependências.

- `/home/runner/work/datapoliRS/datapoliRS/app/core/redis_client.py`  
  Inicializa cliente Redis e disponibiliza `CacheService` com fallback resiliente.

- `/home/runner/work/datapoliRS/datapoliRS/app/core/dependencies.py`  
  Define dependências FastAPI para conexão de banco, autenticação e usuário atual.

- `/home/runner/work/datapoliRS/datapoliRS/app/core/exceptions.py`  
  Implementa handlers globais de exceção em formato RFC 7807.

## Routers (Camada de API)

- `/home/runner/work/datapoliRS/datapoliRS/app/routers/voting.py`  
  Endpoints de votação e candidatos (busca, votação por número/SQ, foto e lista de cargos).

- `/home/runner/work/datapoliRS/datapoliRS/app/routers/geo.py`  
  Endpoint geoespacial para retorno de GeoJSON de municípios.

- `/home/runner/work/datapoliRS/datapoliRS/app/routers/cabinet.py`  
  Endpoints CRUD de lideranças de gabinete com contexto multi-tenant.

- `/home/runner/work/datapoliRS/datapoliRS/app/routers/auth.py`  
  Endpoint de login para emissão de token JWT (fluxo atual com credencial mock).

## Services (Regra de Negócio)

- `/home/runner/work/datapoliRS/datapoliRS/app/services/tse_service.py`  
  Integração assíncrona com DivulgaCandContas para consulta de candidaturas e detalhes.

- `/home/runner/work/datapoliRS/datapoliRS/app/services/voting_service.py`  
  Orquestra consulta de votação, cálculos analíticos e integração com cache.

- `/home/runner/work/datapoliRS/datapoliRS/app/services/geo_service.py`  
  Orquestra geração/retorno de GeoJSON com estratégia cache-aside.

- `/home/runner/work/datapoliRS/datapoliRS/app/services/cabinet_service.py`  
  Regras de negócio do módulo de gabinete e validações de operações de lideranças.

- `/home/runner/work/datapoliRS/datapoliRS/app/services/auth_service.py`  
  Criação/validação de JWT e funções de hash/verificação de senha.

## Repositories (Acesso a Dados)

- `/home/runner/work/datapoliRS/datapoliRS/app/repositories/candidate_repository.py`  
  Queries para busca de candidatos, consulta por SQ e listagem de cargos.

- `/home/runner/work/datapoliRS/datapoliRS/app/repositories/voting_repository.py`  
  Queries de agregação de votos por município e localização de candidato por número/cargo.

- `/home/runner/work/datapoliRS/datapoliRS/app/repositories/geo_repository.py`  
  Queries geoespaciais (PostGIS), incluindo montagem de FeatureCollection com `ST_AsGeoJSON`.

- `/home/runner/work/datapoliRS/datapoliRS/app/repositories/cabinet_repository.py`  
  Persistência CRUD de lideranças com isolamento estrito por `tenant_id`.

## Schemas (Contratos de Dados)

- `/home/runner/work/datapoliRS/datapoliRS/app/schemas/candidate.py`  
  Modelos Pydantic da resposta detalhada de candidatas e bens declarados.

- `/home/runner/work/datapoliRS/datapoliRS/app/schemas/voting.py`  
  Modelos Pydantic para busca de candidatos e resposta analítica de votação.

- `/home/runner/work/datapoliRS/datapoliRS/app/schemas/leadership.py`  
  Modelos Pydantic de entrada/saída do módulo de lideranças.

- `/home/runner/work/datapoliRS/datapoliRS/app/schemas/user.py`  
  Modelos Pydantic de usuário autenticado e dados de token.

## Frontend Estático

- `/home/runner/work/datapoliRS/datapoliRS/app/static/index.html`  
  Estrutura da interface web (SPA).

- `/home/runner/work/datapoliRS/datapoliRS/app/static/script.js`  
  Lógica da SPA: busca, autocomplete, consumo da API e renderização do mapa com Leaflet.

- `/home/runner/work/datapoliRS/datapoliRS/app/static/style.css`  
  Estilos visuais da interface.

- `/home/runner/work/datapoliRS/datapoliRS/app/static/rs_municipios.json`  
  GeoJSON estático de fallback para renderização de mapa.

## ETL e Scripts de Dados

- `/home/runner/work/datapoliRS/datapoliRS/etl/ingest_tse.py`  
  Pipeline de ingestão de dados eleitorais no banco.

- `/home/runner/work/datapoliRS/datapoliRS/etl/import_municipios_geojson.py`  
  Pipeline de carga geoespacial de municípios.

- `/home/runner/work/datapoliRS/datapoliRS/scripts/processar_votos.py`  
  Script standalone para download/processamento de votos do TSE e geração de JSON consolidado.

## Testes

- `/home/runner/work/datapoliRS/datapoliRS/tests/test_tse_service.py`  
  Testes do serviço de integração com TSE usando mocks HTTP.

- `/home/runner/work/datapoliRS/datapoliRS/tests/test_qa.py`  
  Testes de autenticação/JWT e isolamento de contexto de tenant.

- `/home/runner/work/datapoliRS/datapoliRS/tests/test_sprint2_endpoints.py`  
  Testes de endpoints principais (health, geo, candidatos, votação e gabinete).

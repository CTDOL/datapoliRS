# 🏛️ Missão Operações Especiais: DATAPOLIRS — Suíte de Testes E2E com Playwright (Sprint 6.4): análise profunda, execução contra stack local http://127.0.0.1:3000, ajuste e correção de testes e componentes com falha, garantindo 100% de cobertura funcional crítica e emissão de Relatório de Handover formal na Zona de Pouso

Você está atuando como a unidade de **Operações Especiais (Claude Code)** do ecossistema CTDOL, governado pela âncora `CLAUDE.md` e pelos macro-fluxos [[Fluxo_013_Comissionamento_Sistemas_e_Analise_Legado]] e [[Fluxo_007_Mentoria_Externa]].

---

### 1. Contexto & Estado Consolidado da SSoT (Cofre CTDOL)
- **Projeto Alvo:** `DATAPOLIRS` (Diretório: `/Users/cpinfo/Documents/datapoliRS`)
- **SSoT Central:** `/Users/cpinfo/Documents/COFRE_CTDOL_2026`
- **Domínios & Tags:** indice, datapolirs
- **Stack Tecnológico Homologado & Detectado:** Docker, PostgreSQL/PostGIS, Python FastAPI, DuckDB, Next.js, Alembic, Playwright, Esri Canvas, TypeScript, Tailwind CSS, Leaflet, Vitest, Redis
- **Governança Docker Local & Inicialização:**
- **Porta Canônica Local:** `127.0.0.1:3000` (Frontend) e `127.0.0.1:8000` (API) - Confinamento estrito em `127.0.0.1`.
 - **Política de Boot Local:** `restart: "no"` obrigatório no compose local (sem inicialização automática no boot).
 - **Eliminação de Volumes Anônimos:** Named Volumes explícitos (`datapolirs_frontend_node_data`, `datapolirs_frontend_next_data`, `datapolirs_postgres_data`, `datapolirs_redis_data`).
 - **Orquestrador Canônico:** `Makefile` com alvos `make up`, `make down`, `make test`, `make etl-municipios`, `make etl-tse ano=2022`.
 - **Playbook Universal:** [[DOC_OF_005_Playbook_Universal_Docker_CTDOL]] e [[DOC_005_Playbook_Infra_Docker]].
- **Decisões Arquiteturais Vigentes (ADRs do Projeto):**
- **ADR_001_Plano_Arquitetura_datapoliRS.md** (Proposto): 🏗️ Plano de Arquitetura e Desenvolvimento: datapoliRS
- **ADR_002_MultiTenancy_JWT.md** (Ativo): ADR 002: Arquitetura de Autenticação e Isolamento Multi-Tenant
- **ADR_003_Frontend_Monorepo.md** (Ativo): ADR 003: Fundação Frontend e Padrão Mono-repo
- **ADR_004_Homologacao_QA_Docker.md** (Ativo): ADR 004: Homologação QA e Isolamento via Docker
- **ADR_005_Refatoracao_Seguranca_Frontend.md** (Aceito): ADR 005: Refatoração de Segurança e Performance do Frontend (Zero Trust & Edge)
- **ADR_006_Cookie_HttpOnly_Autenticacao.md** (Aprovado): 📜 ADR 006: Transporte de JWT via Cookie HttpOnly e Proteção XSS
- **ADR_007_MapLibre_DOM_Markers_Gabinete.md** (Aprovado): 📜 ADR 007: Adoção de DOM Markers no MapLibre GL e Registro de Débito Técnico
- **ADR_008_Alembic_Tenants_RBAC.md** (Aprovado): 📜 ADR 008: Adoção de Alembic, Tabela Central de Tenants e RBAC
- **ADR_009_Unificacao_Mapa_Leaflet.md** (Aprovado): 📜 ADR 009: Unificação da Stack de Mapas no Frontend com Leaflet (3 Modos)
- **ADR_010_Emendas_Orcamentarias_e_Legislativo_MultiFonte.md** (Aceito): ADR 010: Módulos de Emendas Orçamentárias e Monitoramento Legislativo Multi-Fonte
- **ADR_011_Blindagem_CI_CD_Migrations_e_Quality_Gates.md** (Aceito): ADR 011: Blindagem da Esteira CI/CD com Migrations Alembic Reais e Quality Gates Frontend
- **ADR_012_Configuracoes_Gabinete_Tenant_Profile_RBAC_Exportacao.md** (Aceito): ADR 012: Módulo de Configurações do Gabinete, Gestão de Membros e Exportação de Dados
- **ADR_013_Parametrizacao_Eleicoes_MultiAno_MultiCargo.md** (Aceito): ADR 013: Parametrização Dinâmica de Pleitos Eleitorais e Suporte Multi-Cargo/Multi-Ano
- **ADR_014_Runtime_Dynamic_Config_Redis_Cache_TTL_RateLimits.md** (Aceito): ADR 014: Configurações Dinâmicas de Sistema em Runtime com Cache Redis e Rate Limiting Editável
- **ADR_015_Blindagem_ZeroTrust_Poda_Git_e_Estrategia_Deploy_OCI.md** (Homologado): 📜 ADR 015: Blindagem Docker Zero-Trust, Poda do Repositório Git e Eleição da VPS OCI para Deploy — *Implementação formal da governança Docker Zero-Trust (ADRs 035 e 036), poda do repositório Git reduzindo o tamanho de **558 MB para 1.8 MB** (recuperação de 99,7%), e eleição da **VPS Oracle (OCI Always Free Ampere A1)** como ambiente exclusivo de hospedagem web, rejeitando terminantemente a VPS CTDOL comercial (HostGator/cPanel).*
- **ADR_016_Refatoracao_Monorepo_Canonico.md** (Homologado): 📜 ADR 016: Refatoração para Monorepo Canônico, Segregação Backend/Frontend e Higienização Sanitária — *Adoção formal do padrão **Monorepo Canônico Simétrico** para o `datapoliRS`, segregando integralmente o backend em `backend/` (`app/`, `alembic/`, `tests/`, `alembic.ini`, `Dockerfile`, `requirements.txt`), encapsulando os dados brutos em `etl/data/`, eliminando artefatos soltos na raiz (`claude-skills.tar.gz`) e arquivando DDLs legados (`sql/`).*
- **ADR_017_Migracao_Basemap_Esri_Dual_Layer_e_Cache_GeoJSON.md** (Homologado): 📜 ADR 017: Migração de Basemap para Esri Canvas Dual-Layer, Invalidação Automática de Cache GeoJSON e Parametrização do ETL — *Substituição compulsória dos tiles de mapa CARTO (`cartocdn.com`) por **Esri Canvas Dual-Layer** (`World_Light_Gray_Base`/`World_Dark_Gray_Base` + overlay de topônimos `World_Light_Gray_Reference`/`World_Dark_Gray_Reference`), implementação de **invalidação automática de cache no Redis** (`geo:rs:municipios:feature_collection`) ao final do ETL de municípios, e **parametrização compulsória por ano** (`--ano`) nos scripts de ingestão de votação.*


---

### 2. Doutrina Arquitetural da BIBLIOTECA (RAG Local CTDOL)
> [!quote] Fundamentos Clássicos & Diretrizes Epistêmicas
🧠 [Resultados para: 'DATAPOLIRS Docker PostgreSQL/PostGIS Python FastAPI DuckDB Clean Architecture Docker']

### 📌 Resultado 1: `[[BIBLIOTECA/_FONTES_BRUTAS/WEB/duckdb-analytics/fonte_oficial.md]]`
**Seção:** 2. Python Integration & Ecosystem Architecture
> ==DuckDB== provides native, high-speed ==Python== bindings with full SQL-92 and extensive PostgreSQL dialect extensions.

```==python==
import ==duckdb==

### 📌 Resultado 2: `[[BIBLIOTECA/_FONTES_BRUTAS/WEB/fastapi-backend/fonte_oficial.md]]`
**Seção:** 2. Idiomatic Architecture: Dependency Injection, Routers & Security
> ```==python==
from ==fastapi== import ==FastAPI==, Depends, HTTPException, status, Response, Request
from ==fastapi==.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import...

### 📌 Resultado 3: `[[REINO_MENTAL/01_ZONAS_DE_POUSO/OUTPUTs_CLAUDE/2026-09-11_Relatorio_Handover_Fluxo_007_v2.1.0_Revisao_Script.md]]`
**Seção:** ✅ Testes Executados
> ...Detectou corretamente ==Python== ==FastAPI==, PostgreSQL, Alembic, Pytest, Next.js, TypeScript, Vitest, ==Docker==, Redis |
| Execução `--dry-run` completa contra o projeto real `==DATAPOLIRS==` | Concluída sem erros...

*(Dica: Caso precise de aprofundamento durante a codificação, você pode reconsultar a Biblioteca clássica via `python3 "/Users/cpinfo/Documents/COFRE_CTDOL_2026/.agents/skills/rag_local/scripts/rag_engine.py" search "<sua_duvida>" --top-k 3`)*

---

### 3. Manifesto Clean Code & Quality Gates Inegociáveis
1. **SOLID & Fail-Fast:** Early Return em condicionais; proibição de blocos 'else' aninhados; interfaces e contratos explícitos.
2. **Docker Local Zero-Trust (ADR 035/036):** Confinamento estrito em `127.0.0.1`, proibição de binds em `0.0.0.0`, política `restart: "no"` e Named Volumes.
3. **Idempotência & Migrations:** Migrations DDL/DML devem ser reversíveis, transacionais e testadas via `alembic upgrade head`.
4. **Validação Sanitária Obrigatória:** Passagem com zero erros nos comandos de verificação: `pytest tests/` (ou `pytest -v`), `npm run test` (Vitest), `npm run lint` e `npm run build` (Type-checking / Frontend).

---

### 4. Roteiro Operacional da Sessão: Suíte de Testes E2E com Playwright (Sprint 6.4): análise profunda, execução contra stack local http://127.0.0.1:3000, ajuste e correção de testes e componentes com falha, garantindo 100% de cobertura funcional crítica e emissão de Relatório de Handover formal na Zona de Pouso
Execute as seguintes etapas sequenciais dentro do repositório para o foco 'Suíte de Testes E2E com Playwright (Sprint 6.4): análise profunda, execução contra stack local http://127.0.0.1:3000, ajuste e correção de testes e componentes com falha, garantindo 100% de cobertura funcional crítica e emissão de Relatório de Handover formal na Zona de Pouso':
1. **Inspeção de Contexto & Dependências:** Valide o estado atual do código antes de iniciar.
2. **Execução Técnica da Demanda:** Realize as alterações necessárias respeitando as ADRs da SSoT.
3. **Validação Sanitária & Testes:** Execute os testes do stack e certifique-se de conformidade total.

---

### 5. Entregável Obrigatório (Handover na Zona de Pouso)
Ao concluir sua análise e trabalho, gere um relatório técnico completo e exaustivo no **Padrão Ouro SLC** com a sua assinatura visual de motor:
`🟣 Claude Code (Operações Especiais)`

Salve o relatório diretamente na Zona de Pouso do cofre no seguinte caminho:
`/Users/cpinfo/Documents/COFRE_CTDOL_2026/REINO_MENTAL/01_ZONAS_DE_POUSO/OUTPUTs_CLAUDE/2026-09-11_Relatorio_Handover_DATAPOLIRS_Suite_de_Testes_E2E_com_Playwright_Sprin.md`

O relatório de handover deve conter:
- Totem Resumo Executivo (`> [!tldr]`)
- Estado Atual do Repositório (Git, Docker, Stack detectado)
- Matriz de Conformidade com as ADRs vigentes
- Diagnóstico de Drift e Débitos Técnicos
- Recomendações e Próximos Passos Prioritários para a SSoT

# 🛡️ Relatório de Estado Real e Auditoria Técnica — datapoliRS

> **Fonte:** leitura direta do código-fonte no repositório `datapoliRS` (branch `main`, commit `79553e9`).
> **Data da auditoria:** 22/08/2026.
> **Método:** inspeção do código, do schema real do banco em execução (`\dt`, `\d`) e dos arquivos de configuração — sem inferência a partir de documentação anterior. Este documento substitui e atualiza o relatório de auditoria anterior (mesma data), incorporando os Sprints 0–3.1 do Master Plan de Regularização.

---

## 1. Visão Geral e Mapa de Funcionalidades Entregues

### Propósito Real do Sistema

O **datapoliRS** é uma plataforma de inteligência eleitoral e gestão de gabinete político para o Rio Grande do Sul. Coexistem dois sistemas no mesmo repositório:

1. **Portal Público de Consulta Eleitoral** — SPA vanilla JS/Leaflet servida pelo FastAPI em `/`, sem autenticação, consultando candidaturas de 2022.
2. **Gabinete Digital** — painel Next.js autenticado, multi-tenant, para gestão de lideranças políticas com geolocalização e visualização cruzada com dados de votação.

**Estágio de maturidade: MVP avançado / pré-homologação.** O núcleo de segurança (auth via cookie `HttpOnly`, RBAC, isolamento multi-tenant com FK real, migrations versionadas, rate limiting no login) está regularizado. Os módulos de negócio centrais — Lideranças, Emendas Orçamentárias e Projetos de Lei (com busca em fontes oficiais: ALRS, Câmara dos Deputados e Senado Federal) — estão codificados e operacionais. Falta cobertura de testes automatizados no frontend e a tela de Configurações do gabinete.

### Matriz de Módulos & Features

**✅ Funcionalidades 100% codificadas e operacionais:**

| Módulo | Onde vive |
|---|---|
| Consulta pública de candidatos (TSE 2022) | `app/static/index.html` + `script.js`, consumindo `/api/v1/candidatos`, `/api/v1/votacao/*` |
| Mapa coroplético de votação (Leaflet, portal público) | `app/static/script.js:196-279` |
| Autenticação (login/logout/me) via cookie `HttpOnly` | [app/routers/auth.py](app/routers/auth.py) |
| RBAC (admin/operador/leitor) | [app/core/dependencies.py:96](app/core/dependencies.py:96) (`require_role`), aplicado em `DELETE /gabinete/liderancas/{id}` |
| Multi-tenancy com FK real (`tb_tenants`) | migration [a1961e63fbe4](alembic/versions/a1961e63fbe4_tb_tenants_e_fk_multi_tenant.py) |
| CRUD de Lideranças Políticas (create/read/update/delete) | [app/routers/cabinet.py](app/routers/cabinet.py) — delete exige `role=admin` |
| Paginação real (`page`/`page_size`) em `GET /gabinete/liderancas` | [app/repositories/cabinet_repository.py](app/repositories/cabinet_repository.py) |
| Mapa Tático unificado — 3 modos (Lideranças / Votação / Visão Cruzada) | [frontend/src/components/map/ElectionMap.tsx](frontend/src/components/map/ElectionMap.tsx), via Leaflet |
| Busca de candidato com debounce alimentando o mapa | [frontend/src/app/(dashboard)/page.tsx](frontend/src/app/(dashboard)/page.tsx) |
| Rate limiting (Redis, fixed window) | `voting`, `geo`, `cabinet`, `amendments`, `legislative`, `tasks` routers, e `auth/login` (5 tentativas/60s) |
| Migrations versionadas (Alembic) | `alembic/versions/` — 6 revisões aplicadas |
| Paginação, busca com debounce e exclusão (role=admin) em Lideranças | [LiderancasTable.tsx](frontend/src/features/liderancas/LiderancasTable.tsx), [useLiderancas.ts](frontend/src/features/liderancas/useLiderancas.ts) |
| Módulo de Emendas Orçamentárias — CRUD completo + KPIs agregados | [app/routers/amendments.py](app/routers/amendments.py), tela [/emendas](frontend/src/app/(dashboard)/emendas/page.tsx) |
| Módulo de Projetos de Lei — busca ao vivo em ALRS/Câmara/Senado, importação idempotente, observadores (lideranças) e tarefas | [app/routers/legislative.py](app/routers/legislative.py), [app/services/legislative_sources.py](app/services/legislative_sources.py), tela [/projetos-lei](frontend/src/app/(dashboard)/projetos-lei/page.tsx) |
| Restauração de sessão (`/auth/me`) no layout do dashboard | [layout.tsx](frontend/src/app/(dashboard)/layout.tsx) — sem isso o `role` (e o botão de admin) sumia a cada F5, já que a store Zustand não é persistida |

**🟡 Funcionalidades parciais ou stubs:**

| Item | Estado |
|---|---|
| Tela "Configurações" | Estática — `"será implementada na próxima Sprint"` ([settings/page.tsx](frontend/src/app/(dashboard)/settings/page.tsx)) — sem escopo definido ainda |
| Fonte oficial da ALRS (Projetos de Lei) | Sem API pública documentada — scraping controlado de HTML server-side (Drupal 9), mais frágil que Câmara/Senado (API REST oficial) |
| Prestação de contas oficial (CEAP/CEAPS/emendas federais via CGU) | Levantado e validado na análise, mas fora do escopo deste MVP — API da CGU exige cadastro prévio de token |

**❌ Funcionalidades não iniciadas:**

| Item | Observação |
|---|---|
| Nível municipal (Câmaras de Vereadores via SAPL) | Sem fonte única nem diretório de quais câmaras do RS expõem API — mapeamento manual necessário antes de integrar |
| Dashboard Executivo de KPIs | Não existe — a rota raiz do gabinete é o Mapa Tático, não um painel de métricas consolidado |
| Testes automatizados de frontend | Nenhum arquivo `.test.`/`.spec.` no projeto — sem Vitest, Jest ou Playwright configurados |
| Refresh token | Login só emite access token de 60 min, sem renovação — usuário precisa logar de novo |

### Atores e Perfis de Acesso

| Perfil | Implementado? | Detalhe |
|---|---|---|
| Anônimo | ✅ | Acessa portal público e rotas `voting`/`geo`, sob rate limit |
| Operador (autenticado) | ✅ | `role='operador'` — acesso total a `gabinete/liderancas` exceto `DELETE` |
| Admin | ✅ | `role='admin'` — mesmo acesso do operador + `DELETE` |
| Leitor | 🟡 | Valor aceito pelo `CHECK` constraint do banco e pela lista de `allowed_roles`, mas **nenhuma rota usa `require_role(["leitor", ...])`** — o papel existe no schema sem comportamento diferenciado no código ainda |

---

## 2. Arquitetura do Frontend (Camada de Apresentação)

### Framework & Roteamento

**Next.js 16.3.1** (App Router), **React 19.2.8**, **TypeScript 5**. Árvore de rotas:

```
frontend/src/app/
├── layout.tsx
├── (auth)/login/page.tsx              # "/login"
└── (dashboard)/
    ├── layout.tsx                     # sidebar + navegação + logout
    ├── page.tsx                       # "/" — Mapa Tático (3 modos)
    ├── liderancas/page.tsx            # "/liderancas" — CRUD
    └── settings/page.tsx              # "/settings" — stub
```

Proteção de rota via [middleware.ts](frontend/src/middleware.ts): checa **presença** do cookie `token` (não valida assinatura — a validação real é delegada ao backend a cada request).

### Gerenciamento de Estado & Hooks

| Item | Onde | Observação |
|---|---|---|
| `useAuthStore` | [stores/useAuthStore.ts](frontend/src/stores/useAuthStore.ts) | Zustand, sem persistência — estado de UI se perde em refresh, mas a sessão real (cookie) sobrevive |
| `useLiderancas` | [features/liderancas/useLiderancas.ts](frontend/src/features/liderancas/useLiderancas.ts) | Hook de dados manual (`useState` + `useEffect`), sem cache entre navegações |
| `api` (Axios) | [services/api.ts](frontend/src/services/api.ts) | `baseURL` de `NEXT_PUBLIC_API_URL`, `withCredentials: true`; interceptor de resposta força logout em `401`/`403` |

### Tratamento de Dados e Cache

- **Sem SWR/React Query** — todo fetch é manual via `useEffect` + `useState`, tanto em `useLiderancas` quanto na página do mapa e na busca de candidatos.
- **Sem deduplicação de requisições** — trocar de candidato rapidamente pode disparar múltiplos fetches concorrentes sem cancelamento (`AbortController` não é usado).
- **Paginação:** o backend agora pagina (`GET /gabinete/liderancas?page=&page_size=`), mas o frontend chama com `page_size=200` fixo e não expõe controles de página — funciona hoje pelo volume baixo de dados, não escalável.

### Componentes Críticos & Bibliotecas Visuais

- **Mapa:** `leaflet` 1.9.4 + `@types/leaflet` — **não** MapLibre GL (foi migrado nesta sessão; camadas WebGL de polígono do MapLibre não renderizavam no ambiente de desenvolvimento, Leaflet usa SVG/Canvas 2D e funciona). `@types/maplibre-gl` ainda consta em `devDependencies` — **dependência de tipos órfã**, sem uso.
- **Estilo:** Tailwind CSS v4 (`@tailwindcss/postcss`), padrão visual "glassmorphism".
- **Animação:** Framer Motion (login, transições).
- **Modais:** `LiderancaFormModal.tsx` — implementação própria, sem lib de modal.
- **Validação de `key` em listas:** correta — `LiderancasTable.tsx` usa `key={l.id_lideranca}` (chave estável), não índice de array.

---

## 3. Arquitetura do Backend (Camada de Aplicação e APIs)

### Estrutura de Camadas

```
app/
├── main.py                # entry point, lifespan, CORS, mount de rotas
├── core/                  # config, database, redis, dependencies (auth/RBAC), bootstrap, rate_limit, exceptions
├── routers/                # camada HTTP — auth, geo, voting, cabinet
├── services/                # orquestração — auth, cabinet, geo, tse, voting
├── repositories/            # SQL parametrizado — cabinet, candidate, geo, voting
└── schemas/                # contratos Pydantic
```

A separação routers → services → repositories é consistente em `voting`, `cabinet` e `geo`. **O módulo `auth` é a exceção**: SQL direto em `routers/auth.py` e `core/dependencies.py`, sem repository próprio para `tb_users` — divergência arquitetural conhecida, não corrigida ainda.

### Tabela Completa de Endpoints da API

| Método | Rota | Descrição | Auth | Request Body | Response |
|---|---|---|---|---|---|
| `GET` | `/health` | Healthcheck | Nenhuma | — | `200 {status,version,environment}` |
| `GET` | `/` | Serve o SPA público | Nenhuma | — | `200` HTML |
| `GET` | `/api/v1/candidatas/rs` | Consulta TSE ao vivo (legado) | Nenhuma | Query: `nome, ano, codigo_eleicao` | `200 CandidataDetalhada` / `404` |
| `GET` | `/api/v1/candidatas/{numero}/votos` | Votos por número (legado) | Nenhuma | — | `200 List[{municipio,votos}]` |
| `POST` | `/api/v1/auth/login` | Login (OAuth2 password, form-data) | Nenhuma | `username, password` | `200 {message}` + `Set-Cookie: token` (`HttpOnly`) / `401` |
| `POST` | `/api/v1/auth/logout` | Logout (limpa cookie) | Cookie/Bearer | — | `200 {message}` |
| `GET` | `/api/v1/auth/me` | Usuário autenticado | Cookie/Bearer | — | `200 {email,tenant_id,role}` / `401` |
| `GET` | `/api/v1/cargos` | Lista cargos eletivos | Nenhuma, rate-limited | — | `200 List[Dict]` |
| `GET` | `/api/v1/candidatos` | Busca multi-cargo | Nenhuma, rate-limited | Query: `termo,cd_cargo,sg_partido,nr_candidato,ano,limite` | `200 List[CandidatoBuscaItem]` |
| `GET` | `/api/v1/candidatos/{sq}/foto` | Proxy de foto TSE | Nenhuma | — | `200` imagem/SVG fallback |
| `GET` | `/api/v1/votacao/candidatos/{sq}/municipios` | Votos por município (via SQ) | Nenhuma | — | `200 VotacaoCandidatoResponse` (cache Redis 24h) |
| `GET` | `/api/v1/votacao/numero/{numero_urna}` | Votos por número de urna | Nenhuma | Query: `cd_cargo,ano` | `200 VotacaoCandidatoResponse` |
| `GET` | `/api/v1/geo/municipios` | GeoJSON dos 496 municípios | Nenhuma, rate-limited | — | `200 FeatureCollection` (cache Redis 7d) |
| `GET` | `/api/v1/geo/municipios/lista` | Lista leve com centróide | Nenhuma, rate-limited | — | `200 List` |
| `POST` | `/api/v1/gabinete/liderancas` | Cria liderança | **JWT**, rate-limited | `LiderancaCreate` | `201 LiderancaResponse` |
| `GET` | `/api/v1/gabinete/liderancas` | Lista paginada | **JWT**, rate-limited | Query: `cd_ibge_7,tp_influencia,is_ativo,page,page_size` | `200 LiderancaPageResponse {items,total,page,page_size,total_pages}` |
| `GET` | `/api/v1/gabinete/liderancas/{id}` | Detalhe | **JWT**, rate-limited | — | `200 LiderancaResponse` / `404` |
| `PUT` | `/api/v1/gabinete/liderancas/{id}` | Atualiza | **JWT**, rate-limited | `LiderancaUpdate` | `200 LiderancaResponse` |
| `DELETE` | `/api/v1/gabinete/liderancas/{id}` | Remove | **JWT + role=admin**, rate-limited | — | `204` / `403` se não-admin |

### Injeção de Dependências e Middlewares

- **DB:** `Depends(getDbConnection)` — conexão do pool `asyncpg` por request.
- **Auth:** `Depends(get_current_user)` decodifica JWT (cookie ou header), revalida `is_active` contra o banco a cada request. `Depends(require_role([...]))` (dependency factory) para RBAC.
- **CORS:** lista explícita via `ALLOWED_ORIGINS`, nunca `*` — obrigatório para o cookie `HttpOnly` funcionar cross-origin.
- **Erros globais (RFC 7807):** `UniqueViolationError`→409, `ForeignKeyViolationError`→422, `DomainException`→configurável, catch-all→500 ([app/core/exceptions.py](app/core/exceptions.py)).
- **Rate limiting:** Redis fixed-window, fail-open se Redis cair, aplicado em `voting`, `geo` e `cabinet` (30 req/s) — **`auth` não tem rate limit**, risco de força bruta no login.

---

## 4. Engenharia de Dados & Persistência (OLTP & OLAP)

### Banco de Dados Relacional

**Migrations versionadas com Alembic** — 3 revisões aplicadas (`alembic_version` confirmado no banco):

1. `a099af5414b9_baseline_schema` — espelha o DDL original (idempotente).
2. `a1961e63fbe4_tb_tenants_e_fk_multi_tenant` — cria `tb_tenants`, backfill dinâmico, FKs.
3. `ba54000227b6_role_rbac_em_tb_users` — coluna `role` + `CHECK` constraint.

`sql/01_init_schema.sql` ainda existe (usado pelo bind-mount `docker-entrypoint-initdb.d` do Postgres em container novo) mas **não é mais a fonte de verdade do schema** — Alembic é.

| Tabela | PK | FKs | Índices notáveis |
|---|---|---|---|
| `tb_eleicoes` | `cd_eleicao` | — | `idx_eleicoes_ano` |
| `tb_municipios` | `cd_ibge_7` | — | `idx_municipios_geom` (**GIST**, espacial), `idx_municipios_nome`, `idx_municipios_tse` |
| `tb_partidos` | `nr_partido` | — | `idx_partidos_sigla` |
| `tb_cargos` | `cd_cargo` | — | — |
| `tb_candidaturas` | `sq_candidato` | `cd_eleicao`, `cd_cargo`, `nr_partido` | `idx_cand_numero_eleicao`, `idx_cand_nome_urna`, `idx_cand_partido` |
| `tb_bens_candidatos` | `id_bem` | `sq_candidato` (CASCADE) | `idx_bens_sq_candidato` |
| `tb_fato_votacao_munzona` | `id_fato` | `cd_eleicao`, `sq_candidato`, `cd_ibge_7` | `idx_fato_cand_mun`, `idx_fato_ibge`, `UNIQUE(cd_eleicao,sq_candidato,cd_tse_municipio,nr_zona)` |
| `tb_gabinete_liderancas` | `id_lideranca` | `cd_ibge_7`, **`tenant_id → tb_tenants` (CASCADE)** | `idx_liderancas_tenant`, `idx_liderancas_municipio` |
| `tb_users` | `id` | **`tenant_id → tb_tenants` (RESTRICT)** | `idx_users_email`, `UNIQUE(email)`, `CHECK(role)` |
| **`tb_tenants`** *(nova)* | `id_tenant` | `nr_partido`, `cd_ibge_base` | — |

PostGIS confirmado ativo (`spatial_ref_sys` presente, `GEOMETRY(MultiPolygon,4326)` em `tb_municipios.geometria`).

### Motores Analíticos / Ingestão em Lote

- **DuckDB** é usado **exclusivamente como motor de ETL batch** ([etl/ingest_tse.py](etl/ingest_tse.py)) — lê `votacao_candidato_munzona_2022_RS.csv` via `read_csv` preguiçoso (sem carregar tudo em RAM), agrega e persiste em lote (`execute_values`, batch 10.000) no PostgreSQL via `psycopg2` síncrono. **Roda fora do event loop da API**, só via `make etl-tse`.
- Em runtime, a API **nunca** toca em CSV/arquivos — tudo já foi ingerido no Postgres.
- **Redis** é cache-aside (não é fonte de dados): GeoJSON de municípios (7d), votação por candidato (24h), lista de cargos (30d). `cabinet` (lideranças) e `auth` **nunca** usam cache — sempre Postgres direto.
- `app/data/votos_rs_2022.json` (artefato órfão da arquitetura anterior) **foi removido** nesta sessão (Sprint 0).

---

## 5. Segurança, Multi-Tenancy e Conformidade (LGPD)

### Isolamento Multi-Tenant

- **`tenant_id` é FK real** para `tb_tenants` desde a migration `a1961e63fbe4` — antes era um UUID solto sem entidade própria.
- **Nunca vem do cliente**: extraído do JWT decodificado (`current_user.tenant_id`) em toda rota de `cabinet.py`. O cliente não pode forjar `tenant_id` via URL/body.
- **Isolamento é disciplina de código**, não Row Level Security do PostgreSQL — cada método do repositório inclui manualmente `WHERE tenant_id = $1`. Um novo endpoint escrito sem essa disciplina vazaria dados entre tenants sem barreira estrutural do banco.
- `fk_lideranca_tenant` é `ON DELETE CASCADE` (apagar tenant apaga lideranças), `fk_user_tenant` é `ON DELETE RESTRICT` (não deixa apagar tenant com usuários) — coerente.

### Ciclo de Autenticação & JWT

- **Algoritmo:** HS256, `SECRET_KEY` obrigatória (sem default — falha o startup se ausente).
- **Payload:** `{sub: email, tenant_id: <uuid>, exp}` — sem `role` no token (o papel é buscado do banco a cada request via `get_current_user`, não confiado do JWT).
- **Transporte:** cookie `HttpOnly; SameSite=Lax; Secure` (apenas em produção) — **não** `localStorage`/Bearer no cliente. Corrigido nesta sessão (antes o token ficava em cookie legível por JS).
- **Validade:** 60 min, sem refresh token.
- **Revalidação:** a cada request, `get_current_user` consulta `tb_users` — usuário desativado (`is_active=false`) perde acesso imediatamente mesmo com token ainda válido.

### Privacidade & LGPD

- **PII armazenado:** `tb_gabinete_liderancas.nm_completo`, `nr_telefone`, `ds_email`, `ds_observacoes` (texto livre). **Sem CPF, endereço completo ou filiação partidária** no schema atual.
- **Sem criptografia em coluna** — todo PII é texto puro no Postgres; a proteção depende do isolamento de rede/acesso ao banco.
- **Sem trilha de auditoria** de quem acessou/alterou dados de terceiros, sem soft-delete (o `DELETE` é físico).
- **Nenhum mecanismo de consentimento** implementado.
- **Conclusão:** abaixo do mínimo esperado para LGPD em produção real com dados de terceiros.

---

## 6. Infraestrutura, Docker & Configurações de Ambiente

### Containerização

`docker-compose.yml` — 4 serviços na rede `datapoli_network`:

| Serviço | Imagem/Build | Porta | Healthcheck |
|---|---|---|---|
| `postgres` | `postgis/postgis:16-3.4` | `5432` | `pg_isready` |
| `redis` | `redis:7-alpine` | `6379` | `redis-cli ping` |
| `api` | build local (`./Dockerfile`) | `8000` | `curl -f localhost:8000/health` — comando roda `alembic upgrade head` antes do `uvicorn` |
| `frontend` | build local (`./frontend/Dockerfile`) | `3000` | sem healthcheck definido |

Volumes de hot-reload no `api` incluem `./alembic` e `./alembic.ini` (migrations editáveis sem rebuild). Frontend usa volumes anônimos para `node_modules`/`.next` (evita o host sobrescrever o install do container).

### Inventário de Variáveis de Ambiente

| Variável | Finalidade |
|---|---|
| `POSTGRES_USER/PASSWORD/DB/HOST/PORT` | Credenciais e endereço do Postgres |
| `DATABASE_URL` / `DATABASE_URL_DOCKER` | DSN completo (variante local vs. rede Docker) |
| `REDIS_HOST/PORT/URL` / `*_DOCKER` | Conexão Redis |
| `PORT` | Porta HTTP da API |
| `ENVIRONMENT` | Controla flag `Secure` do cookie e `--reload` |
| `ALLOWED_ORIGINS` | CORS |
| `SECRET_KEY` | Assinatura JWT — **obrigatória, sem default** |
| `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` | Config JWT |
| `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `ADMIN_TENANT_ID` | Bootstrap do admin — **`ADMIN_PASSWORD` agora obrigatória, sem default** (corrigido no Sprint 0; antes era `"admin123"` hardcoded) |
| `NEXT_PUBLIC_API_URL` | URL da API consumida pelo frontend |

### Suíte de Testes

- **Backend:** `pytest` — 11 testes em 3 arquivos (`test_qa.py`, `test_sprint2_endpoints.py`, `test_tse_service.py`), cobrindo JWT, isolamento multi-tenant, RBAC (`test_delete_lideranca_requer_papel_admin`), CRUD de lideranças, busca/votação, geo. **11/11 passando** contra Postgres/Redis reais.
- **Frontend:** **nenhum teste automatizado** — sem Vitest/Jest/Playwright configurado, `package.json` não tem script `test`.
- **CI:** [.github/workflows/ci.yml](.github/workflows/ci.yml) ativo — sobe Postgres+Redis como services, aplica `sql/01_init_schema.sql` (⚠️ **não roda Alembic** — a esteira de CI ainda usa o script raw, não as migrations, uma divergência entre CI e o fluxo real de deploy via `docker-compose`), roda `pytest` a cada push/PR em `main`/`master`.

---

## 7. Diagnóstico de Débitos Técnicos, Gargalos e Riscos

### Code & Architecture Drifts

| Item | Detalhe | Severidade |
|---|---|---|
| CI aplica `sql/01_init_schema.sql`, não `alembic upgrade head` | Diverge do fluxo real (Docker roda Alembic) — CI não testa as migrations em si, só o schema final coincidentemente igual | 🟡 Média |
| Módulo `auth` sem repository | SQL direto em `routers/auth.py`/`core/dependencies.py`, quebra o padrão do resto do código | 🟢 Baixa |
| `@types/maplibre-gl` órfão | Resquício da migração para Leaflet, dependência de tipos sem uso | 🟢 Baixa |
| Frontend sem paginação real na UI | Backend pagina; frontend ainda usa `page_size=200` fixo como paliativo | 🟡 Média |
| Papel `leitor` sem uso | Existe no `CHECK` constraint e na API (`require_role`), mas nenhuma rota o referencia — RBAC incompleto | 🟢 Baixa |
| Botão de exclusão ausente na UI | API pronta e protegida, mas não exposta na tabela de lideranças | 🟢 Baixa |

### Vulnerabilidades de Segurança

- ✅ **Sem SQL Injection** — todas as queries usam parâmetros posicionais (`$1, $2...`).
- ✅ **CORS restrito**, nunca `*`.
- ✅ **Cookie `HttpOnly`** para o JWT (corrigido nesta sessão).
- 🔴 **`/api/v1/auth/login` sem rate limit** — os demais routers protegidos têm 30 req/s via Redis, `auth` não tem nenhum, abrindo espaço para força bruta de senha.
- 🟡 **Sem RLS no banco** — isolamento multi-tenant depende 100% de disciplina de código, sem barreira estrutural do PostgreSQL.
- 🟡 **Sem criptografia de PII em repouso** e sem trilha de auditoria (relevante para LGPD).

### Gargalos de Performance

- **`GET /api/v1/geo/municipios`** monta os 496 municípios com geometria completa em um payload único — mitigado por cache Redis de 7 dias, mas o *cache miss* inicial é uma consulta `ST_AsGeoJSON` pesada.
- **Frontend sem SWR/React Query** — sem deduplicação de requisições nem cancelamento; trocar de candidato rapidamente no mapa pode empilhar fetches concorrentes.
- **DOM Markers no Leaflet** (lideranças) — aceitável no volume atual (dezenas), degrada com milhares de pontos simultâneos.
- **`page_size=200` fixo no frontend** — não é N+1, mas é uma bomba-relógio de escala: cresce linear com o número de lideranças por tenant, sem paginação real na UI.

### As 3 Maiores Prioridades Técnicas

1. **Rate limiting em `/api/v1/auth/login`** — é o único vetor de força bruta sem nenhuma proteção hoje; correção de escopo pequeno (mesmo padrão já usado em `voting`/`geo`/`cabinet`).
2. **Paginação real na UI de lideranças** (Sprint 3.2 do Master Plan, já planejado) — antes de qualquer gabinete real acumular centenas de lideranças, a tela precisa de controles de página/busca em vez de `page_size=200`.
3. **Alinhar CI com Alembic** — a esteira hoje testa contra `sql/01_init_schema.sql` diretamente, não contra `alembic upgrade head`; qualquer regressão introduzida numa migration não seria pega pelo CI antes de ir para produção.

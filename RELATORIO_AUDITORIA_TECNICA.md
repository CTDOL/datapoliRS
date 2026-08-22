# 🛡️ Relatório de Estado Real e Auditoria Técnica — datapoliRS

> **Fonte:** análise direta do código-fonte no repositório `datapoliRS` (branch `main`, commit `227e5ff` em diante).
> **Data da auditoria:** 22/08/2026.
> **Método:** leitura integral dos módulos de backend, frontend, banco de dados, ETL e infraestrutura — sem inferência a partir de documentação anterior. Onde a documentação legada (`RELATORIO_ENGENHARIA_REVERSA.md`, `MAPA_RESPONSABILIDADE.md`) diverge do código atual, este documento prevalece como Única Fonte de Verdade (SSoT).

---

## 1. Visão Geral e Mapa de Funcionalidades Ativas

### Resumo Executivo do Sistema

O **datapoliRS** é uma plataforma de inteligência eleitoral e gestão de gabinete político para o Rio Grande do Sul, dividida em **dois sistemas coexistentes no mesmo repositório**, com maturidades diferentes:

1. **Portal Público de Consulta Eleitoral** (`app/static/index.html` + `script.js`) — SPA vanilla JS/Leaflet, servido diretamente pelo FastAPI em `/`. Consulta candidaturas de 2022 e exibe mapa coroplético de votação por município. **Maturidade: MVP funcional, estável, não autenticado.**
2. **Gabinete Digital** (Next.js em `frontend/`, API em `/api/v1/gabinete/*` e `/api/v1/auth/*`) — painel autenticado multi-tenant para gestão de lideranças políticas com geolocalização. **Maturidade: MVP em desenvolvimento ativo** — CRUD de lideranças funcional, mas telas como "Configurações" são stubs (`"será implementada na próxima Sprint"`, [settings/page.tsx](frontend/src/app/(dashboard)/settings/page.tsx)).

O sistema **não está pronto para produção com clientes reais** no estado atual: falta paginação em listas, há um default de senha de administrador inseguro no código, e o portal público e o gabinete privado usam duas stacks de mapa completamente diferentes (Leaflet vs. MapLibre) sem nenhuma integração entre si.

### Matriz de Módulos Entregues

| Módulo | Onde vive | Status | Evidência |
|---|---|---|---|
| Consulta pública de candidatos (TSE 2022) | Portal público (`/`) + `app/static/script.js` | ✅ Funcional | Consome `/api/v1/candidatos`, `/api/v1/votacao/*` |
| Mapa coroplético de votação por município (Leaflet) | Portal público | ✅ Funcional | `L.geoJson(geojsonData, {style})` em `script.js:257` |
| Autenticação (login/logout, JWT em cookie `HttpOnly`) | Backend `/api/v1/auth/*` + Next `/login` | ✅ Funcional | [auth.py](app/routers/auth.py) |
| CRUD de Lideranças Políticas | `/api/v1/gabinete/liderancas` + `frontend/src/features/liderancas` | ✅ Funcional (create/read/update; **delete existe na API mas sem botão na UI**) | [cabinet.py](app/routers/cabinet.py), [LiderancasTable.tsx](frontend/src/features/liderancas/LiderancasTable.tsx) |
| Mapa Tático de Lideranças (MapLibre GL) | `frontend/src/app/(dashboard)/page.tsx` | ✅ Funcional, mas **não é o mapa coroplético** — só exibe pontos (markers) das lideranças, sem polígonos de votação | [ElectionMap.tsx](frontend/src/components/map/ElectionMap.tsx) |
| Gestão de Emendas Orçamentárias | — | ❌ **Não existe no código.** Nenhuma tabela, rota, schema ou tela relacionada foi encontrada. |
| Dashboard Executivo (KPIs, indicadores agregados) | — | ❌ **Não existe.** A página raiz do gabinete é o Mapa Tático, não um dashboard de métricas. |
| Configurações do Gabinete | `frontend/src/app/(dashboard)/settings` | 🟡 Stub — tela estática avisando "próxima Sprint" |
| Multi-tenancy (isolamento por gabinete/mandato) | `tb_gabinete_liderancas.tenant_id`, `tb_users.tenant_id` | ✅ Funcional e testado ([test_sprint2_endpoints.py:97](tests/test_sprint2_endpoints.py:97)) |

### Perfis de Acesso e Atores

O código só reconhece **um único perfil de usuário autenticado**, sem RBAC (Role-Based Access Control):

- **Visitante anônimo**: acessa o portal público (`/`, `/api/v1/candidatos`, `/api/v1/votacao/*`, `/api/v1/geo/*`) sem login. Rate-limited a 20 req/s por IP no router de votação.
- **Usuário do Gabinete** (`tb_users`): autentica via `/api/v1/auth/login`, recebe um JWT com `sub` (email) e `tenant_id`. Todo usuário autenticado tem acesso irrestrito a **todas** as rotas de `/api/v1/gabinete/*` — não há distinção de papel (admin vs. operador vs. leitura), nem coluna de `role` no schema `tb_users`.
- **Usuário Admin (bootstrap)**: criado automaticamente no startup (`app/core/bootstrap.py`) a partir de `ADMIN_EMAIL`/`ADMIN_PASSWORD` do `.env` — funcionalmente idêntico a qualquer outro usuário, sem privilégios extras no código.

---

## 2. Arquitetura do Frontend (Next.js / React / TypeScript)

Stack: **Next.js 16.3.1** (App Router, Turbopack), **React 19.2.8**, **TypeScript 5**, **Tailwind CSS v4**, **Zustand 5** (estado global), **Axios 1.19**, **MapLibre GL 6.4**, **Framer Motion 13**.

### Roteamento & Páginas

```
frontend/src/app/
├── layout.tsx                          # Root layout (fontes, providers globais)
├── (auth)/
│   └── login/page.tsx                  # Tela de login (form-data OAuth2 -> POST /auth/login)
└── (dashboard)/
    ├── layout.tsx                      # Sidebar + navegação + logout
    ├── page.tsx                        # "/" — Mapa Tático de Lideranças (MapLibre)
    ├── liderancas/page.tsx             # "/liderancas" — CRUD de lideranças (tabela + modal)
    └── settings/page.tsx               # "/settings" — STUB, não implementado
```

Não há rotas dinâmicas (`[id]`), nem rotas de API internas do Next (`app/api/`) — todo o backend é consumido via Axios diretamente no FastAPI.

**Proteção de rotas** ([middleware.ts](frontend/src/middleware.ts)): roda no Edge, verifica a **presença** do cookie `token` para as rotas `/`, `/liderancas*`, `/settings*` e redireciona para `/login` se ausente. **Não valida a assinatura/expiração do JWT** — isso é delegado ao backend (correto: a validação de segurança real mora no servidor; o middleware é só UX).

### Gerenciamento de Estado e Custom Hooks

| Item | Arquivo | Responsabilidade |
|---|---|---|
| `useAuthStore` | [stores/useAuthStore.ts](frontend/src/stores/useAuthStore.ts) | Zustand store simples: `{ user, isAuthenticated, login(), logout() }`. Sem persistência (`persist` middleware não usado) — estado se perde em refresh de página, mas a sessão real (cookie `HttpOnly`) sobrevive. |
| `useLiderancas` | [features/liderancas/useLiderancas.ts](frontend/src/features/liderancas/useLiderancas.ts) | Hook de dados: `fetchLiderancas`, `addLideranca`, `updateLideranca`, `isLoading`, `isSubmitting`. **Sem paginação** — busca a lista inteira em toda chamada. Sem `deleteLideranca` (apesar de a API expor `DELETE`). |
| `api` (Axios instance) | [services/api.ts](frontend/src/services/api.ts) | `baseURL` de `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`), `withCredentials: true`. Interceptor de resposta: em `401`/`403`, força logout local e redireciona para `/login`. |

Não há Context API customizado nem React Query/SWR — busca de dados é feita manualmente com `useEffect` + `useState` em cada componente (`(dashboard)/page.tsx`, `useLiderancas.ts`), sem cache entre navegações.

### Engenharia de Mapas

**Duas bibliotecas de mapa diferentes coexistem no repositório, sem relação entre si:**

| | Portal Público (`app/static/script.js`) | Gabinete Digital (`ElectionMap.tsx`) |
|---|---|---|
| Biblioteca | **Leaflet.js** (via CDN) | **MapLibre GL JS 6.4** (WebGL) |
| Renderização de dados | `L.geoJson()` com polígonos de município (coroplético, cor por votação) | `maplibregl.Marker` — **DOM Markers via `<div>`**, não WebGL layers |
| Fonte de dados | `/api/v1/geo/municipios` (GeoJSON via PostGIS) | `/api/v1/gabinete/liderancas` (pontos de lideranças) |

- **Markers do gabinete são DOM (`document.createElement('div')`)**, não canvas/WebGL — para o volume atual (dezenas/centenas de lideranças) isso é aceitável; se o volume crescer para milhares, DOM markers degradam performance (cada marker é um nó real na árvore do DOM, recalculado a cada evento de mapa).
- **Stale closures**: não identificado — o `useEffect` de criação de markers ([ElectionMap.tsx:104](frontend/src/components/map/ElectionMap.tsx:104)) recria todos os markers do zero a cada mudança de `liderancas`, removendo os antigos via `querySelectorAll('.lideranca-marker')` antes. Correto, embora ineficiente (destrói/recria em vez de fazer diff).
- **Dependência de `useEffect` via `JSON.stringify(liderancas)`** ([linha 148](frontend/src/components/map/ElectionMap.tsx:148)) é um workaround reconhecido pelo próprio ESLint (`react-hooks/exhaustive-deps`) — funciona, mas é O(n) extra a cada render só para comparar deps.
- **Perda de contexto de tema**: já foi um bug conhecido e corrigido — há um comentário extenso no código ([linhas 119-123](frontend/src/components/map/ElectionMap.tsx:119)) documentando que a propriedade CSS `scale` do Tailwind v4 conflitava com o `transform` inline do MapLibre, fazendo os pontos "pularem" da posição ao passar o mouse. A correção (separar elemento de posicionamento do elemento de hover) já está aplicada.
- **Troca de tema (`dark`/`light`)** chama `map.setStyle()`, o que **recarrega os tiles do zero** — não há transição suave, mas não é um bug, é uma limitação conhecida do MapLibre.

### Componentes Visuais e Animações

- **Tailwind CSS v4** (via `@tailwindcss/postcss`) — estilo "glassmorphism" consistente em toda a UI (login, sidebar, cards).
- **Framer Motion** usado em transições de entrada (login, mensagens de erro).
- **Modais**: `LiderancaFormModal.tsx` (150 linhas) — modal de criação/edição controlado por estado local, sem lib de modal (Radix/Headless UI).
- **Validação de `key` em listas**: correta — `LiderancasTable.tsx:26` usa `key={l.id_lideranca}` (chave estável do banco, não índice do array).

---

## 3. Arquitetura do Backend (Python FastAPI / Microsserviço)

### Estrutura de Pastas

```
app/
├── main.py                    # Entry point, lifespan, CORS, mount de rotas e static
├── core/
│   ├── config.py              # Settings (Pydantic Settings, lê .env)
│   ├── database.py            # Pool asyncpg (PostgreSQL/PostGIS)
│   ├── redis_client.py        # Cliente Redis assíncrono + CacheService (fail-open)
│   ├── dependencies.py        # Depends: getDbConnection, get_current_user (JWT)
│   ├── bootstrap.py           # Cria usuário admin idempotente no startup
│   ├── rate_limit.py          # RateLimiter (fixed window, Redis)
│   └── exceptions.py          # Handlers globais RFC 7807
├── routers/                   # Camada HTTP (adaptador de entrada)
│   ├── auth.py, geo.py, voting.py, cabinet.py
├── services/                  # Casos de uso / regra de orquestração
│   ├── auth_service.py, cabinet_service.py, geo_service.py, tse_service.py, voting_service.py
├── repositories/              # Acesso a dados (SQL parametrizado)
│   ├── cabinet_repository.py, candidate_repository.py, geo_repository.py, voting_repository.py
├── schemas/                   # Contratos Pydantic (request/response)
│   ├── candidate.py, geo.py, leadership.py, user.py, voting.py
└── data/
    └── votos_rs_2022.json     # ⚠️ Artefato órfão — 7,6 MB, não referenciado por nenhum código Python ativo (resquício da arquitetura anterior, pré-PostgreSQL)
```

A separação routers → services → repositories é **consistente e real** em `voting`, `cabinet` e `geo`. O módulo `auth` é a exceção: SQL cru direto em `routers/auth.py` e `core/dependencies.py`, sem repository próprio para `tb_users`.

### Tabela Completa de Endpoints da API

| Método | Rota | Descrição | Auth | Request Body | Resposta |
|---|---|---|---|---|---|
| `GET` | `/health` | Healthcheck (Docker probe) | Nenhuma | — | `200` `{status, version, environment}` |
| `GET` | `/` | Serve o SPA público (`index.html`) | Nenhuma | — | `200` HTML |
| `GET` | `/api/v1/candidatas/rs` | Consulta direta ao TSE (compatibilidade legada) | Nenhuma | Query: `nome`, `ano`, `codigo_eleicao` | `200 CandidataDetalhada` / `404` |
| `GET` | `/api/v1/candidatas/{numero}/votos` | Votos de candidato (legado, redirecionado ao Postgres) | Nenhuma | — | `200 List[{municipio, votos}]` |
| `POST` | `/api/v1/auth/login` | Login (OAuth2 password flow, form-data) | Nenhuma | `username`, `password` (form) | `200` `{message}` + `Set-Cookie: token` (`HttpOnly`) / `401` |
| `POST` | `/api/v1/auth/logout` | Logout (limpa cookie no servidor) | Cookie ou Bearer | — | `200 {message}` |
| `GET` | `/api/v1/auth/me` | Dados do usuário autenticado | Cookie ou Bearer | — | `200 {email, tenant_id}` / `401` |
| `GET` | `/api/v1/cargos` | Lista cargos eletivos | Nenhuma (rate-limited 20/s) | — | `200 List[Dict]` |
| `GET` | `/api/v1/candidatos` | Busca candidatos multi-cargo com filtros | Nenhuma (rate-limited) | Query: `termo, cd_cargo, sg_partido, nr_candidato, ano, limite` | `200 List[CandidatoBuscaItem]` |
| `GET` | `/api/v1/candidatos/{sq_candidato}/foto` | Proxy de foto oficial TSE com fallback SVG | Nenhuma | — | `200` imagem/SVG |
| `GET` | `/api/v1/votacao/candidatos/{sq_candidato}/municipios` | Distribuição de votos por município (via SQ) | Nenhuma | — | `200 VotacaoCandidatoResponse` |
| `GET` | `/api/v1/votacao/numero/{numero_urna}` | Distribuição de votos por número de urna | Nenhuma | Query: `cd_cargo, ano` | `200 VotacaoCandidatoResponse` |
| `GET` | `/api/v1/geo/municipios` | GeoJSON completo dos 496 municípios (PostGIS `ST_AsGeoJSON`, cache Redis 7d) | Nenhuma | — | `200 FeatureCollection` |
| `GET` | `/api/v1/geo/municipios/lista` | Lista leve de municípios com centróide | Nenhuma | — | `200 List` |
| `POST` | `/api/v1/gabinete/liderancas` | Cria liderança | **Sim (JWT)** | `LiderancaCreate` | `201 LiderancaResponse` |
| `GET` | `/api/v1/gabinete/liderancas` | Lista lideranças do tenant (sem paginação) | **Sim (JWT)** | Query: `cd_ibge_7, tp_influencia, is_ativo` | `200 List[LiderancaResponse]` |
| `GET` | `/api/v1/gabinete/liderancas/{id}` | Detalhe de uma liderança | **Sim (JWT)** | — | `200 LiderancaResponse` / `404` |
| `PUT` | `/api/v1/gabinete/liderancas/{id}` | Atualiza liderança | **Sim (JWT)** | `LiderancaUpdate` | `200 LiderancaResponse` |
| `DELETE` | `/api/v1/gabinete/liderancas/{id}` | Remove liderança | **Sim (JWT)** | — | `204` |

Todas as rotas `/gabinete/*` são isoladas por `tenant_id` extraído do JWT — nunca aceito via input do cliente.

### Middlewares e Dependências

- **Injeção de dependências**: `Depends(getDbConnection)` (conexão do pool asyncpg por request), `Depends(get_current_user)` (decodifica JWT do cookie/header e valida usuário ativo no banco).
- **Exceções globais** (RFC 7807 Problem Details): `UniqueViolationError` → 409, `ForeignKeyViolationError` → 422, `DomainException` customizada → status configurável, catch-all → 500.
- **CORS**: `CORSMiddleware` com `allow_origins` = lista explícita de `settings.ALLOWED_ORIGINS` (nunca `*`), `allow_credentials=True` — obrigatório para o cookie `HttpOnly` funcionar cross-origin (`:3000` → `:8000`).
- **Rate limiting**: só aplicado ao router de `voting` (20 req/s por IP+tenant, fixed window no Redis, fail-open se Redis cair). **`geo` e `cabinet` não têm rate limit.**
- **Logs**: `logging` padrão do Python, formatado com timestamp/nível/logger, sem correlação de request-id nem integração com APM.

---

## 4. Engenharia de Dados, Persistência e Motor Analítico

### Banco Relacional / Transacional (PostgreSQL 16 + PostGIS 3.4)

Não há Alembic nem sistema de migrations versionadas — o schema é um único script DDL idempotente (`CREATE TABLE IF NOT EXISTS`), aplicado automaticamente no primeiro boot do container Postgres via `docker-entrypoint-initdb.d`. **Isso significa que alterações de schema em produção exigiriam migração manual — não há trilha de versionamento.**

| Tabela | PK | FKs | Campos críticos |
|---|---|---|---|
| `tb_eleicoes` | `cd_eleicao` (VARCHAR) | — | `ano_eleicao`, `tp_abrangencia`, `dt_eleicao` |
| `tb_municipios` | `cd_ibge_7` (VARCHAR 7) | — | `cd_tse` (UNIQUE), `geometria GEOMETRY(MultiPolygon, 4326)` — índice **GIST** |
| `tb_partidos` | `nr_partido` (INT) | — | `sg_partido`, `nm_partido` |
| `tb_cargos` | `cd_cargo` (INT) | — | `ds_cargo` |
| `tb_candidaturas` | `sq_candidato` (BIGINT) | `cd_eleicao → tb_eleicoes`, `cd_cargo → tb_cargos`, `nr_partido → tb_partidos` | `nr_candidato`, `vl_total_bens`, `st_reeleicao` |
| `tb_bens_candidatos` | `id_bem` (UUID) | `sq_candidato → tb_candidaturas ON DELETE CASCADE` | `vl_declarado` |
| `tb_fato_votacao_munzona` | `id_fato` (BIGSERIAL) | `cd_eleicao`, `sq_candidato`, `cd_ibge_7 → tb_municipios` | `qt_votos_nominais`; `UNIQUE(cd_eleicao, sq_candidato, cd_tse_municipio, nr_zona)` — evita duplicidade na carga ETL |
| `tb_gabinete_liderancas` | `id_lideranca` (UUID) | `cd_ibge_7 → tb_municipios` | **`tenant_id` (UUID, NOT NULL, sem FK)** — isolamento multi-tenant; `nr_telefone`, `ds_email` (PII) |
| `tb_users` | `id` (UUID) | — | **`tenant_id` (UUID, sem FK)**; `email UNIQUE`; `hashed_password` |

Observações:
- `tenant_id` em `tb_users` e `tb_gabinete_liderancas` **não tem foreign key para uma tabela `tb_tenants`/`tb_gabinetes`** — não existe uma tabela central de tenants no schema. O "tenant" é apenas um UUID convencional, sem entidade própria, sem nome de gabinete, sem metadados.
- Índice `GIST` em `tb_municipios.geometria` está correto para consultas espaciais performáticas.
- `tb_candidaturas.foto_url` é `TEXT` mas na prática o backend **ignora esse campo e busca a foto ao vivo via proxy HTTP ao TSE** ([voting.py:30](app/routers/voting.py:30)) — coluna potencialmente morta.

### Motor Analítico e Ingestão de Dados

**DuckDB é usado exclusivamente como motor de ETL batch, não como motor de consulta em runtime da API.**

- **Fonte bruta**: `votacao_candidato_munzona_2022_RS.csv` (321 MB, extraído de `votacao.zip` se necessário) — dados oficiais do TSE, **não versionados no Git** (fora do `.gitignore` mas presentes localmente no disco do desenvolvedor).
- **Pipeline** ([etl/ingest_tse.py](etl/ingest_tse.py)): DuckDB abre uma `VIEW` sobre o CSV via `read_csv()` **sem carregar o arquivo inteiro em RAM** (leitura colunar preguiçosa), agrega/transforma, e persiste em lote (`execute_values`, `BATCH_SIZE=10000`) no PostgreSQL via `psycopg2` **síncrono** (fora do event loop da API — roda como script `make etl-tse`, não em request HTTP).
- **Municípios/GeoJSON** ([etl/import_municipios_geojson.py](etl/import_municipios_geojson.py)): lê `app/static/rs_municipios.json` inteiro em memória com `json.load()` e insere as geometrias no PostGIS via `ST_GeomFromGeoJSON`.
- **Em runtime**, a API **nunca** toca em CSV/JSON de dados eleitorais — tudo já foi ingerido no Postgres antes do deploy, e as consultas são SQL parametrizado puro. A agregação de votos por município (`SUM(qt_votos_nominais) GROUP BY município`) é feita **no PostgreSQL**, não em DuckDB nem em memória do processo Python ([voting_repository.py](app/repositories/voting_repository.py)).
- **Exceção**: `app/data/votos_rs_2022.json` (7,6 MB) é um artefato órfão da arquitetura anterior — não é lido por nenhum router/service ativo hoje.

---

## 5. Segurança, Multi-Tenancy e Governança (LGPD)

### Mecanismo de Multi-Tenancy

- **Isolamento por coluna `tenant_id`** em toda query, aplicado manualmente em cada método do repositório — **não é Row Level Security (RLS) do PostgreSQL**, é disciplina de código. Exemplo: [cabinet_repository.py:57](app/repositories/cabinet_repository.py:57) sempre inclui `l.tenant_id = $1` nas condições WHERE.
- O `tenant_id` do request **nunca vem do cliente** — é extraído do JWT decodificado (`current_user.tenant_id`) em toda rota de `cabinet.py`. Isso previne o vetor mais óbvio de vazamento cross-tenant (cliente forjando `tenant_id` na URL/body).
- **Risco residual**: como o isolamento depende de cada query individualmente incluir o filtro, um novo endpoint escrito sem essa disciplina vazaria dados entre tenants silenciosamente — não há um mecanismo de banco (RLS) que barre isso estruturalmente.

### Autenticação e JWT

- **Payload do token** ([auth_service.py:25](app/services/auth_service.py:25)): `{sub: email, tenant_id: <uuid-str>, exp: <timestamp>}`. Sem `iat`, `jti`, `role` ou `scope`.
- **Algoritmo**: HS256 (`settings.ALGORITHM`), assinado com `SECRET_KEY` — **variável obrigatória, sem default no código** (`config.py:36`, falha o startup se ausente). Correto.
- **Expiração**: 60 minutos (`ACCESS_TOKEN_MAX_AGE_SECONDS` em `auth.py`), sem mecanismo de refresh token — usuário precisa logar de novo após 1h.
- **Transporte**: cookie `HttpOnly; SameSite=Lax; Secure=(apenas em produção)`, setado pelo servidor no login — JavaScript do cliente nunca acessa o valor do token (corrigido nesta sessão de trabalho; anteriormente o token ficava em cookie legível por JS).
- **Verificação**: `get_current_user` decodifica o JWT, revalida contra o banco (`SELECT ... FROM tb_users WHERE email = $1 AND tenant_id = $2`) a cada request — garante que um usuário desativado (`is_active=false`) perde acesso imediatamente, mesmo com token ainda válido.

### Conformidade LGPD

- **Dados sensíveis armazenados**: `tb_gabinete_liderancas` guarda `nm_completo`, `nr_telefone`, `ds_email`, `tp_influencia` e `ds_observacoes` (texto livre, pode conter qualquer anotação sobre a pessoa). **Não há campo de CPF, endereço completo ou filiação partidária no schema atual** — apesar de mencionados no prompt de auditoria, esses campos **não existem** no código.
- **Nenhuma criptografia em nível de coluna** — todos os campos, incluindo PII, são colunas de texto puro no Postgres. A proteção depende inteiramente do isolamento de acesso à rede/banco.
- **Nenhum mecanismo de consentimento, anonimização ou direito ao esquecimento** implementado — `DELETE` na API remove o registro fisicamente (hard delete), o que atende "direito à eliminação" na prática, mas não há auditoria de quem apagou o quê nem soft-delete com trilha.
- **Logs**: nenhum dado de PII de lideranças aparece nos logs estruturados do backend (bom), mas o e-mail do usuário autenticado (`ADMIN_EMAIL`) aparece em log de bootstrap — exposição mínima e aceitável.
- **Conclusão**: o sistema está **abaixo do mínimo esperado para LGPD em produção real** — falta política de retenção, criptografia de PII em repouso, e trilha de auditoria de acesso a dados de terceiros.

---

## 6. Infraestrutura, Docker e Configurações de Ambiente

### Contêineres e Orquestração

`docker-compose.yml` define 4 serviços na rede `datapoli_network`:

| Serviço | Imagem/Build | Porta | Volumes | Healthcheck |
|---|---|---|---|---|
| `postgres` | `postgis/postgis:16-3.4` | `5432:5432` | `postgres_data` (dados), `./sql:/docker-entrypoint-initdb.d:ro` (schema) | `pg_isready` |
| `redis` | `redis:7-alpine` | `6379:6379` | `redis_data` | `redis-cli ping` |
| `api` | build local (`./Dockerfile`) | `8000:8000` | `./app`, `./etl`, `./sql`, `./tests`, `./scripts` (hot reload via `--reload`) | `curl -f localhost:8000/health` |
| `frontend` | build local (`./frontend/Dockerfile`) | `3000:3000` | `./frontend:/app` + volumes anônimos p/ `node_modules`/`.next` (preserva install do container) | — (sem healthcheck definido) |

**Dockerfile da API**: `python:3.11-slim`, instala `curl` (p/ healthcheck), `pip install -r requirements.txt`, `COPY . .`, roda `uvicorn` com porta configurável via `$PORT`.

**Dockerfile do Frontend** (adicionado nesta sessão): `node:22-alpine`, `npm install` (não `npm ci` — ver Débitos Técnicos), `npm run dev` (Turbopack com hot reload).

### Inventário de Variáveis de Ambiente (`.env.example`)

| Variável | Finalidade |
|---|---|
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | Credenciais do container Postgres |
| `POSTGRES_HOST` / `POSTGRES_PORT` | Endereço de conexão (nome do serviço Docker) |
| `DATABASE_URL` / `DATABASE_URL_DOCKER` | DSN completo de conexão asyncpg (variante local vs. dentro da rede Docker) |
| `REDIS_HOST` / `REDIS_PORT` / `REDIS_URL` / `REDIS_URL_DOCKER` | Conexão com o cache Redis |
| `PORT` | Porta HTTP da API (default 8000, sobrescrita pelo Render/Netlify em deploy) |
| `PYTHONUNBUFFERED` | Garante flush imediato de logs em containers |
| `ENVIRONMENT` | `development`/`production` — controla flag `Secure` do cookie e `--reload` do uvicorn |
| `ALLOWED_ORIGINS` | Lista de origens permitidas no CORS (separadas por vírgula) |
| `SECRET_KEY` | Chave de assinatura JWT — **obrigatória, sem default** |
| `ALGORITHM` | Algoritmo JWT (HS256) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Validade do token (não usado atualmente — o valor real está hardcoded em `auth.py` como 3600s) |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` / `ADMIN_TENANT_ID` | Usuário administrador criado automaticamente no boot — **`ADMIN_PASSWORD` tem default inseguro `"admin123"` no código** (`config.py:42`) se a env var não for definida |

### Scripts de Build e Testes

| Comando | Ação |
|---|---|
| `make install` | `pip install -r requirements.txt` |
| `make docker-up` | `docker compose up -d --build` — sobe os 4 serviços |
| `make etl` | Roda `import_municipios_geojson` + `ingest_tse` (carga inicial de dados) |
| `make test` / `pytest -v --asyncio-mode=auto` | Suíte backend — **10 testes**, cobre auth/JWT, tenant isolation, endpoints de geo/votação/gabinete |
| `make run` | `uvicorn app.main:app --reload` fora do Docker |
| CI (`.github/workflows/ci.yml`) | GitHub Actions: sobe Postgres+Redis como *services*, aplica `sql/01_init_schema.sql`, roda `pytest` a cada push/PR em `main`/`master` |

**Frontend**: `npm run dev` / `npm run build` / `npm run lint` (`next lint`). **Não há framework de teste configurado no `package.json`** (sem Jest, Vitest, Playwright ou Testing Library) — **zero testes automatizados no frontend.**

---

## 7. Diagnóstico de Débitos Técnicos, Gargalos e Riscos

### Divergências Arquiteturais (Drifts)

| Item | Descrição | Severidade |
|---|---|---|
| **Senha admin default insegura** | `ADMIN_PASSWORD: str = "admin123"` em `config.py:42`, versionado no histórico público do GitHub. Se o deploy não sobrescrever a env var, um admin com senha conhecida é criado automaticamente. | 🔴 Alta |
| **Duas stacks de mapa sem integração** | Leaflet (portal público, coroplético) vs. MapLibre GL (gabinete, pontos) — nenhum reaproveitamento de código, nenhuma ponte entre o mapa de votação e o mapa de lideranças. Um usuário do gabinete não vê os dados eleitorais espacializados junto das lideranças. | 🟡 Média |
| **`npm ci` quebrado no frontend** | O `package-lock.json` não resolve a dependência opcional `@img/sharp-wasm32 → @emnapi/runtime` para a plataforma Linux (foi gerado só em macOS). O Dockerfile usa `npm install` como contorno, o que **não garante build reprodutível** entre ambientes. | 🟡 Média |
| **Sem paginação em `/gabinete/liderancas`** | `useLiderancas` e o repositório trazem a lista inteira sempre — funciona hoje (dezenas de registros), mas não escala para centenas/milhares de lideranças por gabinete. | 🟡 Média |
| **Sem tabela central de tenants** | `tenant_id` é um UUID solto, sem FK, sem entidade `tb_tenants`/`tb_gabinetes` — não há onde guardar nome do gabinete, plano contratado, data de expiração, etc. Bloqueia qualquer feature de billing/gestão de contas. | 🟡 Média |
| **Sem RBAC** | Todo usuário autenticado tem acesso total às rotas do gabinete — não há distinção entre admin do gabinete e operador. | 🟡 Média |
| **`app/data/votos_rs_2022.json` órfão** | 7,6 MB versionado (ou presente em disco) sem nenhum consumidor no código ativo. | 🟢 Baixa |
| **`tb_candidaturas.foto_url` não utilizado** | Coluna existe no schema mas o backend busca a foto ao vivo via proxy TSE, ignorando o campo. | 🟢 Baixa |
| **Sem migrations versionadas** | Um único `CREATE TABLE IF NOT EXISTS` — qualquer alteração de schema em produção precisa de script manual, sem histórico nem rollback. | 🟡 Média |

### Gargalos de Performance & Memory Leaks

- **`votacao_candidato_munzona_2022_RS.csv` (321 MB) e `votacao.zip` (556 MB)** ficam no disco de trabalho — não afetam a API em runtime (só o script ETL), mas se algum processo tentar `open()` ingênuo (sem streaming) nesses arquivos fora do pipeline DuckDB, é risco real de OOM. O pipeline atual (DuckDB `read_csv` lazy) está correto.
- **`GeoJsonFeatureCollection` completa em memória**: `GET /api/v1/geo/municipios` monta os 496 municípios com geometria completa em um único payload JSON — mitigado por cache Redis de 7 dias (TTL alto, geometria é estática), mas o *cache miss* inicial gera uma consulta `ST_AsGeoJSON` pesada no Postgres.
- **Rate limiting só no router de votação**: `/api/v1/gabinete/*` e `/api/v1/geo/*` não têm limite de requisições — sob concorrência alta ou abuso, essas rotas podem sobrecarregar o pool de conexões Postgres (`min_size=2, max_size=20` em `database.py`) sem proteção.
- **DOM Markers no MapLibre**: aceitável no volume atual; centenas de lideranças simultâneas no mapa começam a degradar o *reflow* do navegador (cada marker é manipulação real de DOM, não desenho em canvas).
- **Sem cache/paginação no frontend**: cada navegação para `/liderancas` refaz o fetch completo — sem SWR/React Query, não há deduplicação de requisições concorrentes nem revalidação em background.

### Vulnerabilidades e Pontos de Atenção

- ✅ **Sem SQL Injection**: todas as queries usam parâmetros posicionais (`$1, $2...`) via `asyncpg`, inclusive nas buscas com `ILIKE`/`unaccent`.
- ✅ **CORS restrito**: nunca usa `allow_origins=["*"]`.
- 🔴 **`ADMIN_PASSWORD` default fraco** (já detalhado acima) — risco real se esquecido no deploy.
- 🟡 **Falta de rate-limiting em `/gabinete/*` e `/geo/*`** — só `voting` está protegido.
- 🟡 **Sem validação de força de senha** no cadastro/alteração — o sistema não tem endpoint de troca de senha ainda, mas quando existir, não há regra definida.
- 🟢 **Inputs validados via Pydantic** em todos os endpoints com body (schemas com `min_length`, `max_length`) — mitiga entradas malformadas.
- 🟡 **Sem CSRF explícito**: como a autenticação migrou para cookie, e o cookie usa `SameSite=Lax` (não `Strict`), requisições GET cross-site "top-level" ainda enviam o cookie — mas como todas as mutações do gabinete são `POST/PUT/DELETE` via XHR/fetch (não formulários HTML simples), o risco prático de CSRF é baixo, mas não há um token CSRF dedicado como camada extra.

---

## 8. Próximos Passos de Engenharia Recomendados

1. **Eliminar o default inseguro de `ADMIN_PASSWORD`** — remover o valor `"admin123"` de `config.py` e fazer o campo obrigatório (igual `SECRET_KEY`), falhando o startup se ausente. É a única vulnerabilidade de severidade alta encontrada e o menor esforço de correção da lista.

2. **Criar entidade `tb_tenants`/`tb_gabinetes`** com FK real a partir de `tb_users.tenant_id` e `tb_gabinete_liderancas.tenant_id` — pré-requisito para qualquer evolução de billing, RBAC por gabinete, ou onboarding de múltiplos clientes reais (hoje "tenant" é só um UUID solto).

3. **Introduzir RBAC mínimo** (`role` em `tb_users`: `admin` / `operador`) — antes de vender a plataforma para gabinetes reais, é necessário diferenciar quem pode cadastrar/excluir lideranças de quem só consulta.

4. **Adicionar paginação real em `/api/v1/gabinete/liderancas`** (`limit`/`offset` ou cursor) e no hook `useLiderancas` — hoje escala mal além de algumas centenas de registros por tenant.

5. **Formalizar migrations versionadas** (Alembic) substituindo o script único `sql/01_init_schema.sql` — necessário antes do primeiro deploy em produção com dados reais, para permitir evolução de schema sem downtime ou perda de histórico.

**Adicional (não bloqueante, mas de alto valor de produto):** unificar as duas experiências de mapa — hoje o gabinete autenticado não visualiza os dados eleitorais coropléticos que o portal público já tem prontos; integrar isso no `ElectionMap.tsx` (usando os mesmos dados de `/api/v1/geo/municipios`) entregaria o "Mapa Tático" completo que o nome da tela promete.

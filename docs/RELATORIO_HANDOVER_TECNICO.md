# Relatório de Handover Técnico — datapoliRS

**Documento:** SSoT de Governança Técnica
**Autor:** Arquitetura/Tech Lead (sessão de engenharia assistida)
**Data de emissão:** 2026-08-23
**Commit de referência (`HEAD`):** `53878aa` — `fix: gera tipos de rota do Next.js antes do typecheck no CI`
**Branch:** `main` (`origin/main` sincronizado, sem commits pendentes)

---

## 1. 🎯 Resumo Executivo do Marco

Nesta sessão o pipeline de CI/CD do datapoliRS saiu de um estado **falso-positivo silencioso** (testava contra um schema divergente do deploy real) para **100% verde e representativo do ambiente de produção**, com dois jobs independentes rodando em todo `push`/`pull_request` para `main`/`master`:

| Job | Runner | Etapas | Resultado |
|---|---|---|---|
| `test` (backend) | `ubuntu-latest` + services `postgres` (PostGIS 16-3.4) e `redis` | checkout → setup Python 3.11 → `pip install -r requirements.txt` → **`alembic upgrade head`** → `pytest -v --asyncio-mode=auto` | ✅ 11/11 testes |
| `frontend` (novo, criado nesta sessão) | `ubuntu-latest` | checkout → setup Node 20 → `npm ci` → `npm run lint` → `next typegen` → `tsc --noEmit` → `npm run test` (Vitest) → `playwright install --with-deps chromium` → `npx playwright test` | ✅ lint (0 erros, 6 warnings pré-existentes), typecheck limpo, 2/2 Vitest, 2/2 Playwright |

Execução real validada no GitHub Actions: **run `32672819300`**, ambos os jobs `✓ completed`.

### Volume publicado em `origin/main`

**10 commits** publicados nesta sessão (`git log -n 10`):

```
53878aa fix: gera tipos de rota do Next.js antes do typecheck no CI
4ec285e fix: corrige pipeline de CI que quebrou ao trocar para Alembic
508522e feat: Sprint 5 — CI/CD, alinha pipeline com Alembic e adiciona Vitest/Playwright
ca3df1f fix: corrige bugs encontrados na revisão de código do MVP de Projetos de Lei
a4cb9b6 docs: atualiza auditoria técnica com Emendas, Projetos de Lei e Sprint 3.2
523d942 feat: MVP de Projetos de Lei — busca em fontes oficiais, observadores e tarefas
57e4ef2 feat: Sprint 4 — módulo de Emendas Orçamentárias (CRUD completo + tela /emendas)
08aca52 feat: Sprint 3.2 — rate limiting no login, busca/paginação e exclusão admin em Lideranças
a780265 chore(skills): sincroniza correções da skill arquitetura-hexagonal
7a962c6 refactor: update technical audit report to reflect codebase maturity, RBAC, features
```

### Impacto em confiabilidade e arquitetura

- **CI deixou de mentir sobre o estado do banco.** Antes desta sessão, o pipeline aplicava um dump SQL estático (`sql/01_init_schema.sql`) desatualizado; ele nem continha `tb_tenants`, então 6 dos 11 testes existentes já **erravam silenciosamente por `ERROR` de setup** (mascarado, não aparecia como regressão de feature). Isso significava que o CI nunca havia de fato validado nenhuma migration escrita desde a introdução do multi-tenancy.
- **Divergência CI × Deploy real eliminada.** O `docker-compose.yml` já rodava `alembic upgrade head` como comando de boot da API há tempo; o CI agora espelha exatamente esse fluxo, fechando um gap documentado no `RELATORIO_AUDITORIA_TECNICA.md`.
- **Frontend ganhou rede de segurança automatizada pela primeira vez** — antes desta sessão, nenhum job de CI tocava o diretório `frontend/`.
- **Isolamento multi-tenant reforçado**: um vazamento real de dado entre gabinetes (tenants) foi identificado e corrigido (ver Bug 3).

---

## 2. 🐛 Root Cause Analysis (RCA) dos 5 Bugs Corrigidos

Todos os 5 bugs foram encontrados por uma revisão de código estruturada (8 ângulos de análise: correção linha-a-linha, comportamento removido, rastreamento cross-file, reuso, simplificação, eficiência, altitude arquitetural, convenções) sobre o diff `origin/main..HEAD` no commit `ca3df1f`.

---

### Bug 1 — Crash de import do Senado (ementa nula viola `NOT NULL`)

- **Arquivo:** [app/services/legislative_sources.py](app/services/legislative_sources.py) — classe `SenadoAdapter.buscar_detalhe`
- **Causa raiz:** o adaptador do Senado Federal monta o payload de importação a partir de `proposicao.model_dump(...)`, repassando o campo `ementa` tal como vem da API pública `/dadosabertos/processo`. Diferente dos adaptadores da Câmara e da ALRS — que já tratavam ausência de ementa com um fallback textual — o Senado não tinha esse tratamento. Quando a API retorna uma matéria sem ementa, `ementa=None` seguia até `LegislativeRepository.importarProjetoLei`, cuja coluna `ementa TEXT NOT NULL` (migration `1dac719b2ee7`) rejeita `NULL`, disparando `asyncpg.PostgresError` → `RuntimeError` → **HTTP 500 genérico**, em vez do 502 "não foi possível confirmar na fonte oficial" que todo o resto do fluxo de revalidação usa.
- **Solução técnica aplicada:**
  ```python
  encontrados = await self.buscar_por_nome(autor, limite=100)
  for proposicao in encontrados:
      if proposicao.identificador_externo == identificador_externo:
          dados = proposicao.model_dump(exclude={"fonte", "identificador_externo", "ja_importado", "id_projeto_lei"})
          dados["ementa"] = dados.get("ementa") or "(ementa não disponível na fonte oficial)"
          return dados
  return None
  ```
  Alinha o `SenadoAdapter` ao mesmo contrato defensivo que `CamaraAdapter`/`AlrsAdapter` já cumpriam.
- **Teste que previne regressão:** ainda **não há teste automatizado dedicado** para este caminho (os adaptadores de fontes externas não têm suíte própria — ver Seção 8, item pendente). A correção foi validada manualmente lendo o contrato do schema (`ProjetoLeiImport`) e a constraint da migration. **Risco residual documentado.**

---

### Bug 2 — TypeError potencial no parsing do Senado

- **Arquivo:** [app/services/legislative_sources.py](app/services/legislative_sources.py) — `SenadoAdapter.buscar_por_nome`
- **Causa raiz:** após obter `response.json()`, o código fazia `materias[:limite]` assumindo incondicionalmente que a API do Senado sempre devolve uma lista JSON. Um payload de erro/vazio com HTTP 200 (formato comum em APIs "dados abertos" de governo) retorna um **objeto**, não uma lista — `dict[:limite]` levanta `TypeError: unhashable type: 'slice'`, que não é subclasse de `httpx.HTTPError` e portanto **escapava do único `except` existente**.
- **Solução técnica aplicada:**
  ```python
  if not isinstance(materias, list):
      logger.warning(f"Resposta inesperada do Senado para '{nome}': {materias!r}")
      return []
  ```
  Guard-clause explícita antes do slice, com log estruturado em vez de crash silencioso ou exceção não tratada.
- **Teste que previne regressão:** mesmo caso do Bug 1 — validação manual de tipo, sem suíte automatizada para os adaptadores externos (dependência de rede real dificulta teste determinístico sem `respx`/mocks dedicados — gap identificado para sprint futura).

---

### Bug 3 — Vazamento entre tenants em tarefas (Tenant Isolation Breach)

- **Arquivo:** [app/services/task_service.py](app/services/task_service.py) — `TaskService.createTarefa` / `TaskService.updateTarefa`
- **Severidade:** 🔴 **a mais alta dos 5** — quebra de isolamento multi-tenant, o invariante de segurança central da plataforma.
- **Causa raiz:** `createTarefa` já validava que `id_projeto_lei` e `id_emenda` pertenciam ao tenant do usuário autenticado antes de gravar, mas **não fazia a mesma checagem para `id_lideranca_responsavel`**. A tabela `tb_gabinete_tarefas` só tem uma FK simples para `tb_gabinete_liderancas(id_lideranca)` — sem cláusula de `tenant_id` na própria constraint (ver Seção 4). Um usuário autenticado do Tenant A podia, portanto, enviar o UUID de uma liderança pertencente ao Tenant B (UUIDs são enumeráveis por tentativa/OSINT) e o INSERT era aceito. `TaskRepository.listTarefas`/`getTarefaById` fazem `LEFT JOIN tb_gabinete_liderancas`, então o **nome da liderança de outro gabinete** vazava de volta na resposta da API.
- **Solução técnica aplicada** — validação explícita em ambos os métodos, reaproveitando `CabinetRepository.getLeadershipById` (que já impõe `WHERE tenant_id = $1`):
  ```python
  if payload.id_lideranca_responsavel:
      lideranca = await CabinetRepository.getLeadershipById(connection, tenantId, payload.id_lideranca_responsavel)
      if not lideranca:
          raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Liderança responsável não encontrada neste gabinete.")
  ```
  Aplicado simetricamente em `createTarefa` (payload `TarefaCreate`) e `updateTarefa` (payload `TarefaUpdate`, onde o campo também é editável).
- **Teste que previne regressão:** ⚠️ **gap real** — não há teste automatizado cobrindo especificamente este caso (isolamento cruzado de `id_lideranca_responsavel` em tarefas). O padrão existente de teste multi-tenant (`test_gabinete_liderancas_multi_tenancy_crud` em `tests/test_sprint2_endpoints.py`) cobre isolamento de **Lideranças**, mas não foi replicado para o módulo de Tarefas. **Recomendação prioritária para a próxima sprint de qualidade.**

---

### Bug 4 — Badge "já importado" incorreto acima de 500 PLs

- **Arquivo:** [app/services/legislative_service.py](app/services/legislative_service.py) — `LegislativeService.buscarExterno`
- **Causa raiz:** para marcar quais resultados de busca externa (ALRS/Câmara/Senado) já haviam sido importados pelo gabinete, o método chamava `LegislativeRepository.listProjetosLei(page=1, pageSize=500)` — reaproveitando o método de listagem paginada da UI, com um limite hardcoded de 500 registros. Gabinetes com mais de 500 projetos de lei já importados perdiam silenciosamente a marcação `ja_importado=True` para os registros mais antigos (fora da primeira página), fazendo o botão "Importar" reaparecer como se o item nunca tivesse sido importado.
- **Impacto era limitado por design** (não causava duplicação de dado: a importação usa `ON CONFLICT (tenant_id, fonte, identificador_externo) DO UPDATE`), mas gerava uma UX incorreta e escalava mal.
- **Solução técnica aplicada:** novo método de repositório dedicado, sem paginação, retornando apenas as colunas de deduplicação:
  ```python
  # app/repositories/legislative_repository.py
  @staticmethod
  async def listChavesImportadas(connection, tenantId) -> List[Dict[str, Any]]:
      query = "SELECT fonte, identificador_externo, id_projeto_lei FROM tb_gabinete_projetos_lei WHERE tenant_id = $1;"
      ...
  ```
  `buscarExterno` passou a chamar `listChavesImportadas` em vez de `listProjetosLei(pageSize=500)`, eliminando o cap.
- **Teste que previne regressão:** ⚠️ nenhum teste de integração cobre volumetria alta (>500 registros) — validado apenas por leitura de código e inspeção da query. Testar isso de forma realista exigiria popular o banco com massa de dados, o que não existe hoje na suíte.

---

### Bug 5 — Página presa após exclusão do último item (não exclusivo de Lideranças)

- **Arquivos:** [frontend/src/features/liderancas/useLiderancas.ts](frontend/src/features/liderancas/useLiderancas.ts), replicado em `frontend/src/features/emendas/useEmendas.ts` e `frontend/src/features/projetosLei/useProjetosLei.ts`
- **Causa raiz:** ao excluir o único item restante de uma página não-inicial (ex.: página 2 de 2), o hook chamava `refetch()` mantendo o número de página corrente (`page=2`) — mas o backend, agora com um item a menos, calcula `total_pages=1`. A resposta paginada volta com `items: []`, e a tela renderiza "Nenhuma liderança encontrada" com "Página 2 de 1" e o botão "Próxima" desabilitado, deixando o usuário preso numa página vazia sem recuo automático.
- **Solução técnica aplicada** — os três hooks passaram a inspecionar o resultado do refetch pós-exclusão e recuar uma página quando ela vier vazia:
  ```typescript
  // frontend/src/features/liderancas/useLiderancas.ts
  const deleteLideranca = async (id: string) => {
    ...
    await api.delete(`/api/v1/gabinete/liderancas/${id}`);
    const resultado = await fetchLiderancas(page, termo);
    if (resultado && resultado.items.length === 0 && page > 1) {
      const paginaAnterior = page - 1;
      setPage(paginaAnterior);
      await fetchLiderancas(paginaAnterior, termo);
    }
    ...
  };
  ```
  `fetchLiderancas`/`fetchEmendas`/`fetchProjetosLei` foram ajustadas para **retornar** o payload da resposta (antes só atualizavam state via `setState`), permitindo essa checagem síncrona.
  Em paralelo (bug correlato, mesmo commit), a **primeira carga da página** deixou de esperar o debounce de busca de 350ms — usava incondicionalmente `setTimeout(..., DEBOUNCE_MS)` mesmo no mount inicial sem termo digitado, atrasando todo primeiro carregamento em ~350ms sem necessidade. Corrigido com uma ref `isFirstRender` que dispara o fetch imediatamente no mount.
- **Teste que previne regressão:** ✅ **coberto** — [frontend/src/features/liderancas/useLiderancas.test.ts](frontend/src/features/liderancas/useLiderancas.test.ts), suíte Vitest com `renderHook`/`@testing-library/react` e mock de `@/services/api`:
  - `busca a primeira página imediatamente ao montar, sem esperar o debounce de busca`
  - `recua para a página anterior ao excluir o último item restante de uma página`

  Este é o **único dos 5 bugs com teste de regressão automatizado real** rodando no CI (`frontend` job, etapa "Testes Unitários (Vitest)"). Os padrões equivalentes em `useEmendas.ts`/`useProjetosLei.ts` replicam a mesma lógica mas **não têm teste próprio ainda** — risco de drift se um dos três hooks divergir no futuro sem o outro ser atualizado.

---

## 3. 🚀 Esteira de CI/CD e Garantia de Qualidade (Sprint 5)

### Alembic no CI

Antes: [.github/workflows/ci.yml](.github/workflows/ci.yml) tinha uma etapa `Aplicar Schema do Banco` que rodava `psql -f sql/01_init_schema.sql` diretamente contra o serviço Postgres do runner. Esse arquivo é o **snapshot original** do schema (pré multi-tenancy) e nunca foi atualizado — não contém `tb_tenants`, `tb_gabinete_emendas`, `tb_gabinete_projetos_lei`, `tb_gabinete_projeto_lei_observadores` nem `tb_gabinete_tarefas`.

Depois:
```yaml
- name: Aplicar Migrations (Alembic)
  run: |
    alembic upgrade head
```
O `alembic/env.py` já reaproveita `settings.DATABASE_URL` (a mesma variável de ambiente da aplicação), convertendo o driver para `psycopg2` apenas para a execução síncrona das migrations — nenhuma configuração adicional foi necessária além de garantir `psycopg2-binary`/`alembic` em `requirements.txt` (já presentes).

Isso alinha o CI ao **mesmo comando** que o `docker-compose.yml` já executa como parte do boot do container `api`:
```yaml
command: sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
```

`sql/01_init_schema.sql` permanece no repositório apenas como bootstrap do volume Docker via `docker-entrypoint-initdb.d` (primeira inicialização de um Postgres vazio); como a migration baseline (`a099af5414b9`) usa `CREATE TABLE IF NOT EXISTS` em tudo, ela é segura de rodar em cima do schema legado sem duplicar nada. **Não é mais a fonte de verdade** — Alembic é.

### Armadilhas de CI superadas

Rodar o pipeline de verdade contra o GitHub Actions (em vez de só validar localmente) revelou 3 problemas que só se manifestavam num ambiente verdadeiramente limpo:

**1. Seed de dados de referência em testes — [tests/conftest.py](tests/conftest.py) (novo)**

Trocar o schema estático por migrations corrigiu o erro `relation "tb_tenants" does not exist`, que antes fazia 6 dos 11 testes falharem no setup (mascarados como `ERROR`, nunca chegavam a executar de fato). Ao corrigir isso, ficou exposto o problema seguinte: 3 testes dependiam de **dados reais do TSE/PostGIS** (`tb_municipios`, `tb_candidaturas`, `tb_fato_votacao_munzona`) normalmente carregados via scripts de ETL manuais — [etl/import_municipios_geojson.py](etl/import_municipios_geojson.py) e [scripts/processar_votos.py](scripts/processar_votos.py) — que nunca rodaram em CI. Um `conftest.py` novo com fixture `session`-scoped e `autouse=True` semeia o mínimo necessário (uma eleição, um município com geometria válida via `ST_GeomFromText`, um partido, um cargo, uma candidatura com `nr_candidato=13123` e um fato de votação), tudo com `ON CONFLICT DO NOTHING` — idempotente tanto num banco CI vazio quanto num banco de desenvolvimento já populado com dados reais.

**2. Sincronização de lockfile npm**

`npm ci` (usado em CI para instalação determinística) falhou com `EUSAGE` porque `frontend/package-lock.json` estava fora de sincronia com `package.json` (faltavam entradas opcionais `@emnapi/runtime`/`@emnapi/core`, provavelmente por uma instalação incremental anterior em ambiente diferente do runner Linux). Resolvido regenerando o lockfile do zero (`rm package-lock.json && npm install`) e validando `npm ci` localmente antes do commit.

**3. Geração de tipos de rotas do Next.js em checkout limpo**

`frontend/src/app/layout.tsx` usa `LayoutProps<"/">` — um tipo global que o Next.js 16 só materializa em `.next/types/` depois de rodar `next dev`, `next build` ou `next typegen` pelo menos uma vez. Localmente esse tipo sempre existia (o dev server já havia rodado), então o problema nunca apareceu em testes manuais — só um checkout genuinamente novo o expõe. Resolvido adicionando `npx next typegen` (comando dedicado, mais leve que um build completo) antes do `tsc --noEmit` no job `frontend`. Validado reproduzindo o cenário exato do CI com `git worktree add --detach` num diretório isolado antes do push final.

### Matriz de Testes Ativos

**Backend — Pytest** (`pytest -v --asyncio-mode=auto`, 11 testes em 3 arquivos):

| Suíte | Testes | Cobertura |
|---|---|---|
| `tests/test_qa.py` | 3 | Geração/decodificação de JWT, rejeição de token inválido (401), isolamento de tenant na extração do usuário atual |
| `tests/test_sprint2_endpoints.py` | 6 | `/health`, GeoJSON de municípios (PostGIS), busca multi-cargo de candidatos, votação por número eleitoral, CRUD completo de Lideranças com isolamento multi-tenant (Tenant A × Tenant B), RBAC de exclusão (operador negado / admin permitido) |
| `tests/test_tse_service.py` | 2 | Serviço de busca de candidatas do TSE (sucesso e não-encontrado) |

**Frontend — Lint + Typecheck + Vitest + Playwright:**

| Camada | Ferramenta | Escopo atual |
|---|---|---|
| Lint | ESLint 9 (`eslint-config-next`) | Todo `frontend/src` — 0 erros, 6 warnings pré-existentes de `react-hooks/exhaustive-deps` e uso de `window.location.href` |
| Typecheck | `tsc --noEmit` (precedido de `next typegen`) | Todo o projeto TypeScript |
| Unitário/Hooks | Vitest 4 + `@testing-library/react` (jsdom) | 1 arquivo, 2 testes — `useLiderancas.ts` (comportamento de primeira carga e recuo de página pós-exclusão) |
| E2E (smoke) | Playwright 1.62 (Chromium) | 1 arquivo, 2 testes — renderização da tela de login; redirecionamento de rotas protegidas (`/`, `/liderancas`, `/emendas`, `/projetos-lei`) para `/login` sem sessão, validando o `middleware.ts` |

⚠️ **Gap de cobertura conhecido:** os módulos de Emendas e Projetos de Lei (frontend e backend) e os adaptadores de fontes externas (`legislative_sources.py`) **não têm teste automatizado dedicado** — toda a validação até aqui foi manual (curl, browser) ou por revisão de código. Ver Seção 8.

---

## 4. 🗄️ Estrutura Físico-Relacional e Multi-Tenancy

### Migrations Alembic aplicadas (ordem de cadeia, `head` = `fb903633c34c`)

| Revisão | Down-revision | Descrição |
|---|---|---|
| `a099af5414b9` | `None` (baseline) | Schema base: extensões (`uuid-ossp`, `postgis`, `unaccent`), `tb_eleicoes`, `tb_municipios` (PostGIS `GEOMETRY(MultiPolygon,4326)`), `tb_partidos`, `tb_cargos`, `tb_candidaturas`, `tb_bens_candidatos`, `tb_fato_votacao_munzona`, `tb_gabinete_liderancas`, `tb_users` |
| `a1961e63fbe4` | `a099af5414b9` | Introduz `tb_tenants` + converte `tenant_id` solto em FK real em `tb_users`/`tb_gabinete_liderancas`, com backfill dinâmico de tenants órfãos antes do `ALTER TABLE` |
| `ba54000227b6` | `a1961e63fbe4` | Adiciona `role VARCHAR(20)` a `tb_users` com `CHECK (role IN ('admin','operador','leitor'))`, default `'operador'` |
| `1dac719b2ee7` | `ba54000227b6` | `tb_gabinete_emendas` (Emendas Orçamentárias) |
| `fb903633c34c` (**HEAD**) | `1dac719b2ee7` | `tb_gabinete_projetos_lei`, `tb_gabinete_projeto_lei_observadores`, `tb_gabinete_tarefas` |

### Schemas ativos e garantias de isolamento

| Tabela | Chave/Isolamento | FKs relevantes |
|---|---|---|
| `tb_tenants` | `id_tenant UUID PK` | `nr_partido → tb_partidos`, `cd_ibge_base → tb_municipios` (opcionais) |
| `tb_users` | `tenant_id NOT NULL` | `fk_user_tenant → tb_tenants(id_tenant) ON DELETE RESTRICT` — impede apagar um tenant com usuários ativos |
| `tb_gabinete_liderancas` | `tenant_id NOT NULL` | `fk_lideranca_tenant → tb_tenants ON DELETE CASCADE`; `cd_ibge_7 → tb_municipios` (opcional) |
| `tb_gabinete_emendas` | `tenant_id NOT NULL` | `→ tb_tenants ON DELETE CASCADE`; FK opcional de município beneficiário |
| `tb_gabinete_projetos_lei` | `tenant_id NOT NULL` | `→ tb_tenants ON DELETE CASCADE`; `UNIQUE(tenant_id, fonte, identificador_externo)` — chave de deduplicação de importação idempotente |
| `tb_gabinete_projeto_lei_observadores` | join table | `id_projeto_lei → tb_gabinete_projetos_lei ON DELETE CASCADE`, `id_lideranca → tb_gabinete_liderancas ON DELETE CASCADE`; PK composta |
| `tb_gabinete_tarefas` | `tenant_id NOT NULL` | `id_projeto_lei`/`id_emenda → ... ON DELETE CASCADE` (nullable); **`id_lideranca_responsavel → tb_gabinete_liderancas` sem cláusula de tenant na FK** — ver nota de risco abaixo |

> ⚠️ **Nota de risco arquitetural (relacionada ao Bug 3):** nenhuma das FKs de `id_lideranca_responsavel`, `id_lideranca` (observadores), `cd_ibge_7`, `nr_partido` etc. carrega isolamento por `tenant_id` no nível do banco — o Postgres sozinho **não impede** referenciar uma linha de outro tenant. O isolamento multi-tenant hoje é garantido inteiramente na camada de aplicação (services validando `tenant_id` antes de cada gravação), não pelo schema. Isso é um padrão aceitável dado que a maioria das FKs aponta para dados **de referência compartilhados** (municípios, partidos, cargos — dados TSE/IBGE, não sensíveis por tenant), mas para FKs entre **tabelas de gabinete** (como `tb_gabinete_tarefas.id_lideranca_responsavel → tb_gabinete_liderancas`), a garantia de isolamento depende 100% de todo desenvolvedor futuro lembrar de replicar a checagem manual — exatamente a classe de bug que o Bug 3 expôs. Ver Seção 7 (ADR candidato).

Todas as tabelas de gabinete seguem o mesmo padrão de repositório: `WHERE tenant_id = $1 AND <id> = $2` em toda leitura/atualização/exclusão — nunca uma query sem filtro de tenant.

---

## 5. 📡 Mapa de Endpoints e Contratos de API

Autenticação: JWT em **cookie HttpOnly** (`token`, `httponly=True`, `path=/`) definido em `/api/v1/auth/login`; suporte alternativo a header `Authorization: Bearer` (usado pela suíte de testes). Dependência `get_current_user` extrai de qualquer uma das duas fontes.

| Método | Rota | Auth | RBAC | Rate limit | Router |
|---|---|---|---|---|---|
| `POST` | `/api/v1/auth/login` | — | — | **5 req / 60s** (fixed-window, Redis) | [auth.py](app/routers/auth.py) |
| `POST` | `/api/v1/auth/logout` | Cookie | — | herdado do proxy/global | auth.py |
| `GET` | `/api/v1/auth/me` | ✅ | — | — | auth.py |
| `POST` | `/api/v1/gabinete/liderancas` | ✅ | qualquer papel | 30 req/s (router) | [cabinet.py](app/routers/cabinet.py) |
| `GET` | `/api/v1/gabinete/liderancas` | ✅ | qualquer papel | 30 req/s | cabinet.py |
| `GET` | `/api/v1/gabinete/liderancas/{id}` | ✅ | qualquer papel | 30 req/s | cabinet.py |
| `PUT` | `/api/v1/gabinete/liderancas/{id}` | ✅ | qualquer papel | 30 req/s | cabinet.py |
| `DELETE` | `/api/v1/gabinete/liderancas/{id}` | ✅ | **admin** | 30 req/s | cabinet.py |
| `POST` | `/api/v1/gabinete/emendas` | ✅ | qualquer papel | 30 req/s | [amendments.py](app/routers/amendments.py) |
| `GET` | `/api/v1/gabinete/emendas/kpis` | ✅ | qualquer papel | 30 req/s | amendments.py |
| `GET` | `/api/v1/gabinete/emendas` | ✅ | qualquer papel | 30 req/s | amendments.py |
| `GET` | `/api/v1/gabinete/emendas/{id}` | ✅ | qualquer papel | 30 req/s | amendments.py |
| `PUT` | `/api/v1/gabinete/emendas/{id}` | ✅ | qualquer papel | 30 req/s | amendments.py |
| `DELETE` | `/api/v1/gabinete/emendas/{id}` | ✅ | **admin** | 30 req/s | amendments.py |
| `GET` | `/api/v1/gabinete/projetos-lei/buscar-externo` | ✅ | qualquer papel | 30 req/s | [legislative.py](app/routers/legislative.py) |
| `POST` | `/api/v1/gabinete/projetos-lei` | ✅ | qualquer papel | 30 req/s | legislative.py |
| `GET` | `/api/v1/gabinete/projetos-lei` | ✅ | qualquer papel | 30 req/s | legislative.py |
| `GET` | `/api/v1/gabinete/projetos-lei/{id}` | ✅ | qualquer papel | 30 req/s | legislative.py |
| `DELETE` | `/api/v1/gabinete/projetos-lei/{id}` | ✅ | **admin** | 30 req/s | legislative.py |
| `GET` | `/api/v1/gabinete/projetos-lei/{id}/observadores` | ✅ | qualquer papel | 30 req/s | legislative.py |
| `POST` | `/api/v1/gabinete/projetos-lei/{id}/observadores` | ✅ | qualquer papel | 30 req/s | legislative.py |
| `DELETE` | `/api/v1/gabinete/projetos-lei/{id}/observadores/{id_lideranca}` | ✅ | qualquer papel | 30 req/s | legislative.py |
| `POST` | `/api/v1/gabinete/tarefas` | ✅ | qualquer papel | 30 req/s | [tasks.py](app/routers/tasks.py) |
| `GET` | `/api/v1/gabinete/tarefas` | ✅ | qualquer papel | 30 req/s | tasks.py |
| `PUT` | `/api/v1/gabinete/tarefas/{id}` | ✅ | qualquer papel | 30 req/s | tasks.py |
| `DELETE` | `/api/v1/gabinete/tarefas/{id}` | ✅ | qualquer papel *(decisão deliberada — não é dado mestre)* | 30 req/s | tasks.py |
| `GET` | `/api/v1/geo/municipios` | pública | — | 30 req/s | [geo.py](app/routers/geo.py) |
| `GET` | `/api/v1/geo/municipios/lista` | pública | — | 30 req/s | geo.py |
| `GET` | `/api/v1/candidatos` | pública | — | 20 req/s | [voting.py](app/routers/voting.py) |
| `GET` | `/api/v1/candidatos/{sq_candidato}/foto` | pública | — | 20 req/s | voting.py |
| `GET` | `/api/v1/cargos` | pública | — | 20 req/s | voting.py |
| `GET` | `/api/v1/votacao/candidatos/{sq_candidato}/municipios` | pública | — | 20 req/s | voting.py |
| `GET` | `/api/v1/votacao/numero/{numero_urna}` | pública | — | 20 req/s | voting.py |

**Padrão de RBAC:** dependência `require_role(["admin"])` (definida em `app/core/dependencies.py`) usada exclusivamente nos endpoints `DELETE` de dados mestres (Lideranças, Emendas, Projetos de Lei). Tarefas são deliberadamente exceção — item de trabalho do dia-a-dia, não dado mestre.

**Padrão de rate limiting:** `RateLimiter` (fixed-window, Redis, fail-open) de `app/core/rate_limit.py`, declarado como `dependencies=[Depends(RateLimiter(times=X, seconds=Y))]` no nível do `APIRouter` (aplica a todas as rotas do arquivo). Valores hoje são literais duplicados por arquivo (30/1 na maioria, 20/1 em `voting.py`, 5/60 apenas no login) — **candidato a ADR** de centralização (Seção 7).

---

## 6. 🗺️ Estado dos Componentes de Frontend (Next.js 16 + Leaflet)

**Stack:** Next.js 16.3.1 (App Router), React 19.2.8, Zustand 5 (estado global de auth), Tailwind CSS 4, Framer Motion 13, Axios com interceptor de resposta global.

### `ElectionMap.tsx` — [frontend/src/components/map/ElectionMap.tsx](frontend/src/components/map/ElectionMap.tsx) (246 linhas)

- Usa **Leaflet imperativo diretamente** (`import L from 'leaflet'`), não `react-leaflet` — o mapa e suas camadas (`L.TileLayer`, `L.GeoJSON` para o coroplético, array de `L.Marker[]`) são mantidos em `useRef` e manipulados fora do ciclo de render do React, sincronizados via múltiplos `useEffect` (inicialização do mapa, carga assíncrona do GeoJSON de municípios, atualização de tile/tema, atualização de marcadores de lideranças, atualização de camada coroplética por modo de visualização).
- Carregado na página do dashboard (`frontend/src/app/(dashboard)/page.tsx`) via `next/dynamic` com SSR desabilitado — Leaflet depende de `window`/`document`, incompatível com renderização no servidor.
- Consome GeoJSON de `/api/v1/geo/municipios` (backend, PostGIS `ST_AsGeoJSON`) e pontos de liderança das APIs de gabinete.

### `LiderancasTable.tsx` — [frontend/src/features/liderancas/LiderancasTable.tsx](frontend/src/features/liderancas/LiderancasTable.tsx) (138 linhas)

- Tabela server-driven (paginação/busca/filtro resolvidos no backend, não client-side).
- **Padrão de exclusão:** confirmação inline de dois estados por linha (ícone de lixeira → vira par de botões "Confirmar"/"Cancelar" no mesmo lugar), controlado por `confirmandoId` local — **não usa modal nem `window.confirm`**. Replicado identicamente em `EmendasTable.tsx` e `ProjetosLeiTable.tsx`.
- **Não há sistema de notificação/toast no frontend** (`grep` por `toast|Toast|notif` em todo `frontend/src` não retorna nenhum resultado). Erros de rede em qualquer hook (`useLiderancas`, `useEmendas`, `useProjetosLei`, `useProjetoLeiDetalhe`) caem em `console.error(...)` e a função retorna `false`/`null` silenciosamente para o componente decidir — hoje, na prática, a maioria dos componentes **não exibe feedback visual de erro ao usuário**. Gap de UX identificado, não corrigido nesta sessão (fora de escopo).

### Busca com debounce

Padrão consistente (mas duplicado três vezes, sem hook compartilhado — ver Seção 7) em `useLiderancas.ts`, `useEmendas.ts` e `useProjetosLei.ts`: `useRef<ReturnType<typeof setTimeout>>` + `clearTimeout`/`setTimeout(fn, DEBOUNCE_MS)` a cada mudança de termo/filtro, com `DEBOUNCE_MS = 350` (listas) ou `400` (busca externa de proposições em `useProjetosLei.ts`, que exige mínimo de 3 caracteres antes de disparar).

Desde o Bug 5 (Seção 2), a **primeira carga em cada um dos três hooks** é disparada imediatamente via ref `isFirstRender`, sem esperar o debounce.

### Modal de exclusão

Não existe um componente de modal de exclusão dedicado — a confirmação é sempre inline na própria linha da tabela (ver `LiderancasTable.tsx` acima). O único modal real do módulo de Projetos de Lei é [ProjetoLeiDetailModal.tsx](frontend/src/features/projetosLei/ProjetoLeiDetailModal.tsx), que é um modal de **detalhe/gestão** (observadores + tarefas), não de confirmação de exclusão.

---

## 7. ⚖️ Decisões Arquiteturais Emergentes (Candidatas a ADR)

1. **Revalidação server-side obrigatória na importação de dados externos.** `ProjetoLeiImport` (payload do cliente) deliberadamente **não aceita** `ementa`/`situacao` — só campos identificadores (`fonte`, `identificador_externo`, `tipo`, `numero`, `ano`, `autor`). O backend sempre busca de novo na fonte oficial (`adaptador.buscar_detalhe(...)`) antes de persistir. Decisão de segurança: o cliente nunca pode "inventar" o conteúdo de um dado que se apresenta como oficial. Formalizar como ADR explícito, já que qualquer nova fonte de dado externo deveria seguir o mesmo contrato.

2. **Isolamento multi-tenant é responsabilidade da camada de serviço, não do schema.** Como descrito na Seção 4, FKs entre tabelas de gabinete não carregam `tenant_id`. O Bug 3 é evidência direta de que esse padrão é frágil sob esquecimento humano. **ADR recomendado:** avaliar se vale introduzir uma constraint composta (`FOREIGN KEY (tenant_id, id_lideranca) REFERENCES tb_gabinete_liderancas(tenant_id, id_lideranca)`) nas FKs entre tabelas de gabinete, movendo a garantia para o banco — ou, alternativamente, formalizar como regra de code review obrigatória documentada (ex.: em CLAUDE.md/checklist de PR) que toda nova FK para tabela de gabinete exige uma chamada de validação de tenant explícita no service.

3. **CI como ambiente hermético com seed mínimo, não com ETL completo.** Decisão tomada ao corrigir a Armadilha 1 da Seção 3: em vez de rodar os scripts pesados de ETL (`etl/import_municipios_geojson.py`, `scripts/processar_votos.py`) a cada execução de pipeline, o CI semeia apenas o mínimo de dados de referência necessário para os testes existentes passarem. Trade-off consciente: CI rápido e determinístico, mas **não valida o pipeline de ETL em si** — se o ETL quebrar, só será percebido em ambiente real. Vale documentar esse limite explicitamente.

4. **Rate limiting fail-open, por router, com literais duplicados.** `RateLimiter(times=30, seconds=1)` é repetido em 5+ arquivos de router. Funciona hoje, mas não há um único lugar para ver "qual é o limite padrão de escrita" — ADR recomendado: centralizar como constantes nomeadas em `app/core/rate_limit.py` (ex.: `DEFAULT_WRITE_LIMIT`, `LOGIN_LIMIT`) para eliminar o risco de divergência silenciosa entre routers.

5. **Ausência deliberada de sistema de notificação central no frontend.** Até esta sessão, nenhuma tela usa toast/snackbar — erros de API terminam em `console.error`. Não foi uma decisão documentada, é um vácuo de decisão. Recomenda-se elevar a ADR explícito antes do próximo módulo de frontend, para não repetir o padrão de "erro engolido" em código novo.

---

## 8. 📊 Matriz de Maturidade e Próximos Passos

| Área | Status | Observação |
|---|---|---|
| Autenticação (JWT + cookie HttpOnly) | ✅ 100% Homologado | Testado em `test_qa.py`, validado em produção via browser |
| RBAC (`admin`/`operador`/`leitor`) | ✅ 100% Homologado | `CHECK` constraint no banco + `require_role` na API; testado em `test_delete_lideranca_requer_papel_admin` |
| Rate limiting (Redis, fail-open) | ✅ 100% Homologado | Aplicado a login e a todos os routers de gabinete |
| Módulo Lideranças (CRUD + paginação + busca) | ✅ 100% Homologado | Único módulo com teste de hook automatizado (Vitest) além dos testes de API |
| Módulo Emendas Orçamentárias (Sprint 4) | 🟡 Parcial | CRUD + KPIs funcionais e validados manualmente; **sem teste automatizado** (backend ou frontend) |
| Módulo Projetos de Lei (MVP externo) | 🟡 Parcial | Busca ALRS (scraping HTML)/Câmara/Senado (APIs oficiais) + import + observadores + tarefas funcionais; **sem teste automatizado**; ALRS é scraping de HTML não-documentado, frágil a redesign do site oficial |
| Módulo Tarefas | 🟡 Parcial | CRUD funcional; isolamento de tenant para `id_lideranca_responsavel` **corrigido nesta sessão mas sem teste de regressão** (Bug 3) |
| CI/CD (Alembic + Pytest + Lint + Typecheck + Vitest + Playwright) | ✅ 100% Homologado | Validado com execução real no GitHub Actions, run `32672819300` |
| Cobertura de teste — adaptadores de fontes externas (`legislative_sources.py`) | ⏳ Próxima sprint | Nenhum teste unitário isolando `CamaraAdapter`/`SenadoAdapter`/`AlrsAdapter` (via `respx`, já usado em `test_tse_service.py`) |
| Cobertura de teste — isolamento multi-tenant em Tarefas | ⏳ Próxima sprint | Replicar o padrão de `test_gabinete_liderancas_multi_tenancy_crud` para `tb_gabinete_tarefas`, cobrindo especificamente o Bug 3 |
| Sistema de notificação/feedback visual (toast) | ⏳ Próxima sprint | Não iniciado — erros de API hoje só aparecem no console do navegador |
| Escala municipal/União (fora do foco em deputado estadual) | ⏳ Próxima sprint | Mencionado como visão de produto; nenhuma implementação ainda (SAPL/TCE-RS para nível municipal permanece não iniciado) |
| Constraint composta de tenant em FKs de gabinete | ⏳ Avaliação de ADR | Ver Seção 7, item 2 — decisão de arquitetura ainda em aberto |

---

*Fim do relatório. Gerado por inspeção direta do código-fonte, `git log`, migrations Alembic, arquivos de CI e execução real do pipeline no GitHub Actions (run `32672819300`) em 2026-08-23.*

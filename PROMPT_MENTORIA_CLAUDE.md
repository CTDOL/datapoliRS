# 🏛️ Missão Operações Especiais: DATAPOLIRS — Migração Gradual para shadcn/ui: Fase 1 no Módulo de Lideranças (/liderancas) com Blindagem de Testes

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
 - **Orquestrador Canônico:** `Makefile` com alvos `make up`, `make down`, `make test`, `make etl-municipios`, `make etl-tse ano=2022`, `make etl-comparecimento ano=2022`.
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
- **ADR_018_Reverse_Proxy_Nginx_Producao_e_Subdominios.md** (Homologado): 📜 ADR 018: Adoção de Reverse Proxy Nginx para Produção e Segregação por Subdomínios (App vs API) — *Implementação formal de uma camada de **Reverse Proxy com Nginx** dedicada exclusivamente ao ambiente de produção (`docker-compose.prod.yml`), blindando a exposição direta de portas da aplicação (`3000` e `8000`) e roteando o tráfego externo através de **dois subdomínios segregados** (`${APP_DOMAIN}` e `${API_DOMAIN}`) via `envsubst` em portas padrão HTTP/HTTPS (`80`/`443`).*
- **ADR_019_Liderancas_Modelagem_NN_Municipios_e_Upload_Midia.md** (Homologado): 📜 ADR 019: Modelagem N:N de Lideranças por Municípios, Upload Seguro de Mídia e Preservação de Rótulos do TSE — *Evolução do Módulo de Lideranças Políticas de relacionamento 1:N (município único) para **relacionamento N:N** através da tabela associativa `tb_gabinete_lideranca_municipios` (com backfill automático dos registros anteriores), implementação de **upload físico de fotos reais** com validação de tipo/tamanho e expurgo no disco, e enriquecimento do pipeline eleitoral com a coluna `nm_municipio_tse` para erradicar rótulos órfãos em relatórios ("Município 88013" $\rightarrow$ "Porto Alegre").*
- **ADR_020_Blindagem_FullStack_CI_Playwright_e_Confinamento_Loopback.md** (Homologado): 📜 ADR 020: Blindagem Full-Stack do CI/CD com Playwright E2E e Erradicação do Antipadrão Loopback Localhost — *Implementação formal de **serviços reais de backend no runner de CI do Frontend** (`postgis/postgis:16-3.4`, `redis:7-alpine`, `uvicorn` e migrations Alembic), alinhamento compulsório do host de testes Playwright para `127.0.0.1` (erradicando o antipadrão `localhost` cross-host para cookies `HttpOnly`/`SameSite=Lax`), eliminação de condição de corrida na seleção de modo do mapa (`page.tsx`) e desacoplamento do erro `401` da tela de login no interceptor Axios (`api.ts`).*
- **ADR_021_Adocao_Shadcn_UI_e_Contorno_Turbopack_tw_animate.md** (Aceito): 🏛️ ADR 021: Adoção de Matriz de Componentes shadcn/ui sob Tailwind v4 e Contorno do Bug de Resolução no Turbopack — *Homologação do spike técnico que atesta a viabilidade do **`shadcn/ui` (com primitivos `@base-ui/react`) sobre Next.js 16.3 + React 19 + Tailwind CSS v4**, sem qualquer regressão visual ou interferência no motor cartográfico **Leaflet 1.9.4 / Esri Canvas**, condicionada à aplicação do **contorno (*workaround*) de caminho relativo para o `tw-animate-css`** exigido pela limitação do resolvedor de CSS do Turbopack.*


---

### 2. Doutrina Arquitetural da BIBLIOTECA (RAG Local CTDOL)
> [!quote] Fundamentos Clássicos & Diretrizes Epistêmicas
🧠 [Resultados para: 'DATAPOLIRS Docker PostgreSQL/PostGIS Python FastAPI DuckDB Clean Architecture Docker']

### 📌 Resultado 1: `[[DATAPOLIRS/DOC_OF-datapolirs/ADR_016_Refatoracao_Monorepo_Canonico.md]]`
**Seção:** 3. Decisão Tomada
> ...==Clean== ==Architecture== e Governança do Cofre CTDOL:

```text
==datapoliRS==/
├── .claude/               # Governança do Claude Code
├── .github/               # Workflows de CI/CD
├── backend/               # [ENCAPSULADO] Todo o backend ==Python==...

### 📌 Resultado 2: `[[REINO_MENTAL/01_ZONAS_DE_POUSO/OUTPUTs_CLAUDE/2026-09-11_Relatorio_Handover_DATAPOLIRS_Refatoracao_Estrutural_para_Monorepo_Can.md]]`
**Seção:** 1.4 Stack detectado (inalterado)
> ==Docker==, PostgreSQL/PostGIS, ==Python== ==FastAPI==, ==DuckDB==, Next.js, Alembic, Playwright, Pytest, TypeScript, Tailwind CSS, Leaflet, Vitest, Redis — nenhuma dependência foi adicionada, removida ou versionada nesta...

### 📌 Resultado 3: `[[BIBLIOTECA/_FONTES_BRUTAS/WEB/duckdb-analytics/fonte_oficial.md]]`
**Seção:** 2. Python Integration & Ecosystem Architecture
> ==DuckDB== provides native, high-speed ==Python== bindings with full SQL-92 and extensive PostgreSQL dialect extensions.

```==python==
import ==duckdb==

*(Dica: Caso precise de aprofundamento durante a codificação, você pode reconsultar a Biblioteca clássica via `python3 "/Users/cpinfo/Documents/COFRE_CTDOL_2026/.agents/skills/rag_local/scripts/rag_engine.py" search "<sua_duvida>" --top-k 3`)*

---

### 3. Manifesto Clean Code & Quality Gates Inegociáveis
1. **SOLID & Fail-Fast:** Early Return em condicionais; proibição de blocos 'else' aninhados; interfaces e contratos explícitos.
2. **Docker Local Zero-Trust (ADR 035/036):** Confinamento estrito em `127.0.0.1`, proibição de binds em `0.0.0.0`, política `restart: "no"` e Named Volumes.
3. **Idempotência & Migrations:** Migrations DDL/DML devem ser reversíveis, transacionais e testadas via `alembic upgrade head`.
4. **Validação Sanitária Obrigatória:** Passagem com zero erros nos comandos de verificação: `pytest tests/` (ou `pytest -v`), `npm run test` (Vitest), `npm run lint` e `npm run build` (Type-checking / Frontend).

---

### 4. Roteiro Operacional da Sessão: Migração Gradual para shadcn/ui — Fase 1: Módulo de Lideranças (/liderancas)

> [!target] Escopo Delimitado e Risco Zero
> A **Opção A** foi homologada na **ADR 021**. O objetivo desta sessão é modernizar exclusivamente o **Módulo de Lideranças** (`frontend/src/app/(dashboard)/liderancas/`), substituindo a tabela e o modal manuais por componentes oficiais do **shadcn/ui** (`<Table>`, `<Dialog>`, `<Card>`, `<Badge>`, `<Button>`), **mantendo o Mapa Tático (Leaflet 1.9.4) 100% intocado**.

Execute rigorosamente as 5 etapas sequenciais:

#### Etapa 1: Preparação do Ambiente & Branch de Feature
1. O spike técnico anterior validou os componentes e o patch do Turbopack na branch `spike/shadcn-ui-matriz`.
2. A partir da branch `spike/shadcn-ui-matriz` (que já contém `button.tsx`, `card.tsx`, `table.tsx`, `dialog.tsx`, `badge.tsx` em `src/components/ui/` e o patch em `globals.css`), crie a branch de trabalho:
   ```bash
   git checkout spike/shadcn-ui-matriz
   git checkout -b feature/shadcn-liderancas
   ```
3. Confirme que o contorno do Turbopack em `frontend/src/app/globals.css` está ativo:
   ```css
   @import "tailwindcss";
   @import "../../node_modules/tw-animate-css/dist/tw-animate.css";
   @import "shadcn/tailwind.css";
   ```

#### Etapa 2: Refatoração da Tabela de Lideranças (`LiderancasTable.tsx`)
1. Localize o componente `LiderancasTable.tsx` em `frontend/src/components/liderancas/` (ou caminho correspondente).
2. Substitua as tags `<table>`, `<thead>`, `<tbody>`, `<tr>`, `<th>`, `<td>` manuais pelos componentes importados de `@/components/ui/table`:
   ```tsx
   import {
     Table,
     TableBody,
     TableCell,
     TableHead,
     TableHeader,
     TableRow,
   } from "@/components/ui/table"
   import { Badge } from "@/components/ui/badge"
   import { Button } from "@/components/ui/button"
   ```
3. Mantenha 100% intactas todas as regras de negócio: renderização de fotos reais/fallback, lista de municípios (relação N:N sob ADR 019), botões de ação (editar, excluir, WhatsApp `wa.me`) e paginação.

#### Etapa 3: Refatoração do Modal de Cadastro/Edição (`LiderancaFormModal.tsx`)
1. Localize o modal de lideranças.
2. Substitua o overlay/modal manual pelos componentes de diálogo acessíveis do shadcn:
   ```tsx
   import {
     Dialog,
     DialogContent,
     DialogDescription,
     DialogHeader,
     DialogTitle,
     DialogFooter,
   } from "@/components/ui/dialog"
   ```
3. Assegure que o foco automático, fechamento via tecla `Esc` e animações nativas do `@base-ui/react` funcionem suavemente.
4. Mantenha o upload físico de fotos (`FormData`), validação de tamanho/tipo e seleção múltipla de municípios 100% operacionais.

#### Etapa 4: Auditoria de Sigilo Estratégico (Regra 18)
- Em cumprimento estrito à **Regra 18 da Constituição do CTDOL**, certifique-se de que os rótulos de interface, tooltips e mensagens de sucesso utilizem termos corporativos neutros (*"Gestão de Lideranças e Contatos Regionais"*, *"Base Territorial"*), sem qualquer menção a "gabinete", "mandato" ou siglas militares.

#### Etapa 5: Quality Gate Inegociável
Execute a suíte completa de verificação:
```bash
npm run test        # Vitest (2/2)
npm run build       # Next.js Build e Type-checking
npx playwright test # Playwright E2E (13/13 devem permanecer verdes)
```
Se algum teste Playwright falhar por mudança de seletor CSS no modal ou tabela, ajuste o seletor no teste de forma correspondente sem alterar a regra de negócio.

---

### 5. Entregável Obrigatório (Handover na Zona de Pouso)
Ao concluir, gere o relatório técnico completo no **Padrão Ouro SLC** com a sua assinatura visual:
`🟣 Claude Code (Operações Especiais)`

Grave o relatório diretamente na Zona de Pouso do cofre no seguinte caminho:
`/Users/cpinfo/Documents/COFRE_CTDOL_2026/REINO_MENTAL/01_ZONAS_DE_POUSO/OUTPUTs_CLAUDE/2026-09-12_Relatorio_Handover_DATAPOLIRS_Migracao_Shadcn_Liderancas.md`

O relatório de handover deve conter:
- Totem Resumo Executivo (`> [!tldr]`)
- Diff de arquivos refatorados em `frontend/`
- Evidências dos Quality Gates (Playwright 13/13, Vitest 2/2, Next Build)
- Confirmação de integridade do Mapa Tático (Leaflet/Esri intocados)
- Status do Git (branch `feature/shadcn-liderancas` pronta para merge)

# 🏛️ Missão Operações Especiais: datapolirs — esteira cicd paridade hml deploy oci e resolucao de pendencias

Você está atuando como a unidade de **Operações Especiais (Claude Code)** do ecossistema CTDOL, governado pela âncora `CLAUDE.md` e pelos macro-fluxos [[Fluxo_013_Comissionamento_Sistemas_e_Analise_Legado]] e [[Fluxo_007_Mentoria_Externa]].

---

### 1. Contexto & Estado Consolidado da SSoT (Cofre CTDOL)
- **Projeto Alvo:** `datapolirs` (Diretório: `/Users/cpinfo/Documents/datapoliRS`)
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
- **ADR_001_datapolirs_Plano_Arquitetura_datapoliRS.md** (Proposto): 🏗️ Plano de Arquitetura e Desenvolvimento: datapoliRS
- **ADR_002_datapolirs_MultiTenancy_JWT.md** (Ativo): ADR 002: Arquitetura de Autenticação e Isolamento Multi-Tenant
- **ADR_003_datapolirs_Frontend_Monorepo.md** (Ativo): ADR 003: Fundação Frontend e Padrão Mono-repo
- **ADR_004_datapolirs_Homologacao_QA_Docker.md** (Ativo): ADR 004: Homologação QA e Isolamento via Docker
- **ADR_005_datapolirs_Refatoracao_Seguranca_Frontend.md** (Aceito): ADR 005: Refatoração de Segurança e Performance do Frontend (Zero Trust & Edge)
- **ADR_006_datapolirs_Cookie_HttpOnly_Autenticacao.md** (Aprovado): 📜 ADR 006: Transporte de JWT via Cookie HttpOnly e Proteção XSS
- **ADR_007_datapolirs_MapLibre_DOM_Markers_Gabinete.md** (Aprovado): 📜 ADR 007: Adoção de DOM Markers no MapLibre GL e Registro de Débito Técnico
- **ADR_008_datapolirs_Alembic_Tenants_RBAC.md** (Aprovado): 📜 ADR 008: Adoção de Alembic, Tabela Central de Tenants e RBAC
- **ADR_009_datapolirs_Unificacao_Mapa_Leaflet.md** (Aprovado): 📜 ADR 009: Unificação da Stack de Mapas no Frontend com Leaflet (3 Modos)
- **ADR_010_datapolirs_Emendas_Orcamentarias_e_Legislativo_MultiFonte.md** (Aceito): ADR 010: Módulos de Emendas Orçamentárias e Monitoramento Legislativo Multi-Fonte
- **ADR_011_datapolirs_Blindagem_CI_CD_Migrations_e_Quality_Gates.md** (Aceito): ADR 011: Blindagem da Esteira CI/CD com Migrations Alembic Reais e Quality Gates Frontend
- **ADR_012_datapolirs_Configuracoes_Gabinete_Tenant_Profile_RBAC_Exportacao.md** (Aceito): ADR 012: Módulo de Configurações do Gabinete, Gestão de Membros e Exportação de Dados
- **ADR_013_datapolirs_Parametrizacao_Eleicoes_MultiAno_MultiCargo.md** (Aceito): ADR 013: Parametrização Dinâmica de Pleitos Eleitorais e Suporte Multi-Cargo/Multi-Ano
- **ADR_014_datapolirs_Runtime_Dynamic_Config_Redis_Cache_TTL_RateLimits.md** (Aceito): ADR 014: Configurações Dinâmicas de Sistema em Runtime com Cache Redis e Rate Limiting Editável
- **ADR_015_datapolirs_Blindagem_ZeroTrust_Poda_Git_e_Estrategia_Deploy_OCI.md** (Homologado): 📜 ADR 015: Blindagem Docker Zero-Trust, Poda do Repositório Git e Eleição da VPS OCI para Deploy — *Implementação formal da governança Docker Zero-Trust (ADRs 035 e 036), poda do repositório Git reduzindo o tamanho de **558 MB para 1.8 MB** (recuperação de 99,7%), e eleição da **VPS Oracle (OCI Always Free Ampere A1)** como ambiente exclusivo de hospedagem web, rejeitando terminantemente a VPS CTDOL comercial (HostGator/cPanel).*
- **ADR_016_datapolirs_Refatoracao_Monorepo_Canonico.md** (Homologado): 📜 ADR 016: Refatoração para Monorepo Canônico, Segregação Backend/Frontend e Higienização Sanitária — *Adoção formal do padrão **Monorepo Canônico Simétrico** para o `datapoliRS`, segregando integralmente o backend em `backend/` (`app/`, `alembic/`, `tests/`, `alembic.ini`, `Dockerfile`, `requirements.txt`), encapsulando os dados brutos em `etl/data/`, eliminando artefatos soltos na raiz (`claude-skills.tar.gz`) e arquivando DDLs legados (`sql/`).*
- **ADR_017_datapolirs_Migracao_Basemap_Esri_Dual_Layer_e_Cache_GeoJSON.md** (Homologado): 📜 ADR 017: Migração de Basemap para Esri Canvas Dual-Layer, Invalidação Automática de Cache GeoJSON e Parametrização do ETL — *Substituição compulsória dos tiles de mapa CARTO (`cartocdn.com`) por **Esri Canvas Dual-Layer** (`World_Light_Gray_Base`/`World_Dark_Gray_Base` + overlay de topônimos `World_Light_Gray_Reference`/`World_Dark_Gray_Reference`), implementação de **invalidação automática de cache no Redis** (`geo:rs:municipios:feature_collection`) ao final do ETL de municípios, e **parametrização compulsória por ano** (`--ano`) nos scripts de ingestão de votação.*
- **ADR_018_datapolirs_Reverse_Proxy_Nginx_Producao_e_Subdominios.md** (Homologado): 📜 ADR 018: Adoção de Reverse Proxy Nginx para Produção e Segregação por Subdomínios (App vs API) — *Implementação formal de uma camada de **Reverse Proxy com Nginx** dedicada exclusivamente ao ambiente de produção (`docker-compose.prod.yml`), blindando a exposição direta de portas da aplicação (`3000` e `8000`) e roteando o tráfego externo através de **dois subdomínios segregados** (`${APP_DOMAIN}` e `${API_DOMAIN}`) via `envsubst` em portas padrão HTTP/HTTPS (`80`/`443`).*
- **ADR_019_datapolirs_Liderancas_Modelagem_NN_Municipios_e_Upload_Midia.md** (Homologado): 📜 ADR 019: Modelagem N:N de Lideranças por Municípios, Upload Seguro de Mídia e Preservação de Rótulos do TSE — *Evolução do Módulo de Lideranças Políticas de relacionamento 1:N (município único) para **relacionamento N:N** através da tabela associativa `tb_gabinete_lideranca_municipios` (com backfill automático dos registros anteriores), implementação de **upload físico de fotos reais** com validação de tipo/tamanho e expurgo no disco, e enriquecimento do pipeline eleitoral com a coluna `nm_municipio_tse` para erradicar rótulos órfãos em relatórios ("Município 88013" $\rightarrow$ "Porto Alegre").*
- **ADR_020_datapolirs_Blindagem_FullStack_CI_Playwright_e_Confinamento_Loopback.md** (Homologado): 📜 ADR 020: Blindagem Full-Stack do CI/CD com Playwright E2E e Erradicação do Antipadrão Loopback Localhost — *Implementação formal de **serviços reais de backend no runner de CI do Frontend** (`postgis/postgis:16-3.4`, `redis:7-alpine`, `uvicorn` e migrations Alembic), alinhamento compulsório do host de testes Playwright para `127.0.0.1` (erradicando o antipadrão `localhost` cross-host para cookies `HttpOnly`/`SameSite=Lax`), eliminação de condição de corrida na seleção de modo do mapa (`page.tsx`) e desacoplamento do erro `401` da tela de login no interceptor Axios (`api.ts`).*
- **ADR_021_datapolirs_Adocao_Shadcn_UI_e_Contorno_Turbopack_tw_animate.md** (Aceito): 🏛️ ADR 021: Adoção de Matriz de Componentes shadcn/ui sob Tailwind v4 e Contorno do Bug de Resolução no Turbopack — *Homologação do spike técnico que atesta a viabilidade do **`shadcn/ui` (com primitivos `@base-ui/react`) sobre Next.js 16.3 + React 19 + Tailwind CSS v4**, sem qualquer regressão visual ou interferência no motor cartográfico **Leaflet 1.9.4 / Esri Canvas**, condicionada à aplicação do **contorno (*workaround*) de caminho relativo para o `tw-animate-css`** exigido pela limitação do resolvedor de CSS do Turbopack.*
- **ADR_022_datapolirs_Esteira_CICD_Paridade_Producao_Deploy_OCI.md** (Executada / Homologada em HML): 📜 ADR 022: Esteira de CI/CD com Paridade de Produção e Deploy Pull-Based na VPS Oracle (Piloto) — *Instituição de um modelo de **3 branches por ambiente** (`dev` → `hml` → `main`), com promoção `dev→hml` e `hml→main` via Pull Request e o **deploy real em produção disparado exclusivamente por Release publicada** (tag `vX.Y.Z`), consumindo imagens já versionadas no GitHub Container Registry (GHCR) construídas com suporte multi-arquitetura (`linux/amd64,linux/arm64`) para a VPS Oracle Ampere A1.*
- **ADR_023_datapolirs_Setup_Inicial.md** (Aceito): ADR 031: Comissionamento Arquitetural do Projeto datapoliRS
- **ADR_024_datapolirs_Implementacao_Esteira_CICD_e_Correcao_Cookie_Cross_Subdominio.md** (Implementado (código) — pendente configuração humana no GitHub): 📜 ADR 024: Implementação da Esteira de CI/CD (ADR_022) e Correção do Mecanismo de Cookie Cross-Subdomínio — *Implementada a estrutura de branches `dev`→`hml`→`main` (com proteção de PR obrigatório, inclusive para admin) e reestruturado o `ci.yml` conforme a Definition of Done da [[ADR_022_datapolirs_Esteira_CICD_Paridade_Producao_Deploy_OCI]]. **Uma correção técnica foi necessária**: a diretiva `proxy_cookie_domain api.${APP_DOMAIN} ${APP_DOMAIN};` prescrita no §3.3.3 da ADR 022 não funcionaria — o Nginx só *reescreve* um atributo `Domain=` já presente no `Set-Cookie`, nunca *adiciona* um que não existe. O backend precisou emitir explicitamente esse atributo para a borda ter o que reescrever.*
- **ADR_025_datapolirs_Selo_Visual_de_Ambiente_Dev_Hml.md** (Aceito): 📜 ADR 025: Selo Visual de Ambiente (Desenvolvimento/Homologação) na Interface — *Aplicação, no frontend do `datapoliRS`, do padrão universal [[ADR_047_governanca_Selo_Visual_de_Ambiente_em_Interfaces]]: uma faixa visual fixa no topo da interface identifica quando o usuário está em `dev` ("AMBIENTE DE DESENVOLVIMENTO") ou `hml` ("AMBIENTE DE HOMOLOGAÇÃO"), ausente em produção real.*
- **ADR_026_datapolirs_Cookie_Host_Only_via_Rewrite_Same_Origin.md** (Aceita): 📜 ADR 026: Cookie de Sessão *Host-Only* via Reescrita Same-Origin — *O cookie de sessão do datapoliRS passa a ser **host-only** em `datapoli.ctdol.com.br`. O compartilhamento cross-subdomínio implementado na [[ADR_024_datapolirs_Implementacao_Esteira_CICD_e_Correcao_Cookie_Cross_Subdominio]] §2.3 — `proxy_cookie_domain ${API_DOMAIN} ${ROOT_DOMAIN}` mais emissão explícita de `Domain=` pelo backend — é **revogado**.*


---

### 2. Doutrina Arquitetural da BIBLIOTECA (RAG Local CTDOL)
> [!quote] Fundamentos Clássicos & Diretrizes Epistêmicas
🧠 [Resultados para: 'datapolirs Docker PostgreSQL/PostGIS Python FastAPI DuckDB Clean Architecture Docker']

### 📌 Resultado 1: `[[DATAPOLIRS/DOC_OF-datapolirs/ADR_016_datapolirs_Refatoracao_Monorepo_Canonico.md]]`
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

### 4. Roteiro Operacional da Sessão: Diagnóstico e Resolução de Erros da Esteira

> [!important] Modo de Resolução de Erros Ativado (Instrução Prioritária)
> **Atenção Claude Code:** O desenvolvedor vai apresentar erros de execução (do CI, do terminal ou de outra IDE). Sua primeira prioridade é **ler atentamente os logs de erro apresentados, identificar a causa-raiz com precisão cirúrgica e aplicar a correção mínima necessária** sem violar o isolamento do monorepo nem quebrar testes existentes.

> [!bug] Erro Detectado em Tempo Real no CI (Job e2e-parity na branch hml):
> - **Falha:** `frontend/e2e/modulos.spec.ts:13:87`
> - **Mensagem:** `Error: strict mode violation: getByText(/lideranças? no total|Nenhuma liderança encontrada/) resolved to 2 elements`
>   - Elemento 1: `<td colspan="6" ...>Nenhuma liderança encontrada.</td>`
>   - Elemento 2: `<span>0 lideranças no total</span>`
> - **Causa-Raiz:** O seletor regex casou com ambos os elementos simultâneos na página de Lideranças. O Playwright opera em strict mode por padrão e aborta quando `getByText` encontra > 1 elemento.
> - **Correção Prescrita:** Especificar o seletor com precisão, por exemplo:
>   `await expect(page.getByRole('cell', { name: 'Nenhuma liderança encontrada.' })).toBeVisible();`
>   ou isolar o contador específico no footer/card.

#### Etapas da Sessão:

1. **Ingerir e Resolver os Erros Apresentados pelo Desenvolvedor:**
   - Leia atentamente qualquer stack trace, log do Playwright/Pytest ou mensagem de erro que o desenvolvedor colar ou indicar nesta sessão.
   - Aplique o conserto cirúrgico no arquivo afetado (ex: `frontend/e2e/modulos.spec.ts`).

2. **Validar a Suíte Localmente:**
   - Rode o teste afetado para garantir que passou:
     ```bash
     cd frontend && npx playwright test e2e/modulos.spec.ts
     ```

3. **Commit e Push na branch correspondente (`hml` ou `dev`):**
   - Comite com mensagem semântica clara (ex: `fix(e2e): resolve strict mode violation no seletor de liderancas`).
   - Verifique que o pipeline volta a ficar 100% verde no GitHub.

4. **Gerar Relatório de Handover na Zona de Pouso:**
   - Grave seu relatório em `REINO_MENTAL/01_ZONAS_DE_POUSO/OUTPUTs_CLAUDE/2026-09-13_Relatorio_Handover_DATAPOLIRS_Correcao_Erros_CI.md` seguindo o Padrão Ouro SLC.

---

### 5. Entregável Obrigatório (Handover na Zona de Pouso)
Ao concluir sua análise e trabalho, gere um relatório técnico completo e exaustivo no **Padrão Ouro SLC** com a sua assinatura visual de motor:
`🟣 Claude Code (Operações Especiais)`

Salve o relatório diretamente na Zona de Pouso do cofre no seguinte caminho:
`/Users/cpinfo/Documents/COFRE_CTDOL_2026/REINO_MENTAL/01_ZONAS_DE_POUSO/OUTPUTs_CLAUDE/2026-09-13_Relatorio_Handover_datapolirs_esteira_cicd_paridade_hml_deploy_oci_e_r.md`

O relatório de handover deve conter:
- Totem Resumo Executivo (`> [!tldr]`)
- Estado Atual do Repositório (Git, Docker, Stack detectado)
- Matriz de Conformidade com as ADRs vigentes
- Diagnóstico de Drift e Débitos Técnicos
- Recomendações e Próximos Passos Prioritários para a SSoT

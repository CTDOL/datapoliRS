# 🏛️ Missão Operações Especiais: DATAPOLIRS — Correção de Bug Visual na Tela de Login (allowedDevOrigins e Hydration Next 16)

Você está atuando como a unidade de **Operações Especiais (Claude Code)** do ecossistema CTDOL, governado pela âncora `CLAUDE.md` e pelos macro-fluxos [[Fluxo_013_Comissionamento_Sistemas_e_Analise_Legado]] e [[Fluxo_007_Mentoria_Externa]].

---

### 1. Contexto & Estado Consolidado da SSoT (Cofre CTDOL)
- **Projeto Alvo:** `DATAPOLIRS` (Diretório: `/Users/cpinfo/Documents/datapoliRS`)
- **SSoT Central:** `/Users/cpinfo/Documents/COFRE_CTDOL_2026`
- **Domínios & Tags:** indice, datapolirs
- **Stack Tecnológico Homologado & Detectado:** Docker, PostgreSQL/PostGIS, Python FastAPI, DuckDB, Next.js, Alembic, Playwright, Pytest, TypeScript, Tailwind CSS, Leaflet, Vitest, Redis
- **Governança Docker Local & Inicialização:**
- **Porta Canônica Local:** `127.0.0.1:3000` (Frontend) e `127.0.0.1:8000` (API) - Confinamento estrito em `127.0.0.1`.
 - **Política de Boot Local:** `restart: "no"` obrigatório no compose local (sem inicialização automática no boot).
 - **Eliminação de Volumes Anônimos:** Migração dos volumes anônimos de `/app/node_modules` e `/app/.next` para Named Volumes explícitos (`datapolirs_frontend_node_data` e `datapolirs_frontend_next_data`).
 - **Orquestrador Canônico:** `Makefile` ([[Modelo_21_Docker_Compose_e_Makefile_Padrao]]) com alvos `make setup`, `make up`, `make down`, `make logs` e `make healthcheck`.
 - **Playbook Universal:** [[DOC_OF_005_Playbook_Universal_Docker_CTDOL]].
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


---


---

### 🚨 4. Diagnóstico Pericial do Bug & Roteiro de Resolução Cirúrgica

#### O Sintoma:
Ao abrir `http://127.0.0.1:3000/login` no navegador, o usuário vê apenas o fundo degradê escuro. O formulário de login (card, inputs, botão) fica **completamente invisível** (opacidade zero), embora esteja presente no DOM (o clique no centro ativa o tooltip HTML5 *"Preencha este campo."*).

#### Evidência Pericial nos Logs do Contêiner (`datapoli_frontend`):
```text
⚠ Blocked cross-origin request to Next.js dev resource /_next/static/chunks/node_modules_next_dist_... from "127.0.0.1".
Cross-origin access to Next.js dev resources is blocked by default for safety.

To allow this host in development, add it to "allowedDevOrigins" in next.config.js and restart the dev server:

// next.config.js
module.exports = {
  allowedDevOrigins: ["127.0.0.1"],
}
```

#### As Duas Causas Raízes Identificadas:
1. **Bloqueio de Chunks JS pelo Next.js 16 (Turbopack Dev):**
   O Next.js 16 bloqueia requisições cross-origin para recursos de desenvolvimento a partir do host `127.0.0.1` a menos que explicitamente declarado em `allowedDevOrigins` no `frontend/next.config.ts`. Como os chunks JS de hidratação foram bloqueados, **nenhum código React/JS do cliente é executado no navegador**.
2. **Dependência Crítica de Hidratação do Framer Motion:**
   No arquivo `frontend/src/app/(auth)/login/page.tsx`, o card principal está envolvido por:
   `<motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} ...>`
   Como o HTML gerado no SSR é emitido com `opacity: 0`, e os scripts do cliente foram bloqueados pela Causa 1, a animação para `opacity: 1` nunca dispara, deixando a tela invisível para o usuário final.

#### Tarefas de Execução Obrigatórias:
1. **Configurar `allowedDevOrigins` no `frontend/next.config.ts`:**
   Adicionar a propriedade `allowedDevOrigins: ["127.0.0.1", "localhost", "127.0.0.1:3000", "localhost:3000"]` no objeto `nextConfig`.
2. **Blindar `frontend/src/app/(auth)/login/page.tsx` contra Flash Invisível:**
   Assegurar que o formulário não dependa exclusivamente de JS para visibilidade básica (ex: garantir fallback seguro de visibilidade ou transição suave que não deixe o elemento permanente em `opacity: 0` caso a hidratação demore).
3. **Reiniciar o serviço frontend:**
   `docker compose restart frontend` (ou recriar o contêiner se necessário).
4. **Verificar os logs:**
   Garantir via `docker logs datapoli_frontend` que as mensagens de `Blocked cross-origin request` foram completamente eliminadas e que os chunks `200 OK` são servidos.
5. **Executar Testes de Regressão:**
   Rodar a suíte de testes unitários do frontend (`npm run test` com Vitest) dentro de `frontend/` e `pytest tests/` no backend para garantir zero regressão.

### 5. Entregável Obrigatório (Handover na Zona de Pouso)
Ao concluir sua análise e trabalho, gere um relatório técnico completo e exaustivo no **Padrão Ouro SLC** com a sua assinatura visual de motor:
`🟣 Claude Code (Operações Especiais)`

Salve o relatório diretamente na Zona de Pouso do cofre no seguinte caminho:
`/Users/cpinfo/Documents/COFRE_CTDOL_2026/REINO_MENTAL/01_ZONAS_DE_POUSO/OUTPUTs_CLAUDE/2026-09-11_Relatorio_Handover_DATAPOLIRS_Correcao_de_Bug_Visual_na_Tela_de_Login_.md`

O relatório de handover deve conter:
- Totem Resumo Executivo (`> [!tldr]`)
- Estado Atual do Repositório (Git, Docker, Stack detectado)
- Matriz de Conformidade com as ADRs vigentes
- Diagnóstico de Drift e Débitos Técnicos
- Recomendações e Próximos Passos Prioritários para a SSoT

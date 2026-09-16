# 🏛️ Missão Operações Especiais: DATAPOLIRS — Diagnóstico e Correção da Busca de Projetos de Lei nas Fontes Oficiais (ALRS, Câmara e Senado)

Você está atuando como a unidade de **Operações Especiais (Claude Code)** do ecossistema CTDOL, governado pela âncora `CLAUDE.md`, pelos macro-fluxos [[Fluxo_013_Comissionamento_Sistemas_e_Analise_Legado]], [[Fluxo_006_Arquitetura_Alta_Complexidade]] e [[Fluxo_007_Mentoria_Externa]].

---

### 1. Contexto & Estado Consolidado da SSoT (Cofre CTDOL)
- **Projeto Alvo:** `DATAPOLIRS` (Diretório do Monorepo: `/Users/cpinfo/Documents/datapoliRS`)
- **SSoT Central:** `/Users/cpinfo/Documents/COFRE_CTDOL_2026`
- **Domínios & Tags:** `indice`, `datapolirs`, `legislativo`, `scraping`, `resiliencia`
- **Stack Tecnológico Homologado & Detectado:** Docker, PostgreSQL/PostGIS, Python FastAPI, DuckDB, Next.js, Alembic, Playwright, Esri Canvas, TypeScript, Tailwind CSS, Leaflet, Vitest, Redis
- **Governança Docker Local & Inicialização:**
  - **Portas Canônicas:** `127.0.0.1:3000` (Frontend) e `127.0.0.1:8000` (API) - Confinamento estrito em `127.0.0.1`.
  - **Política de Boot Local:** `restart: "no"` obrigatório no compose local (sem inicialização automática no boot).
  - **Eliminação de Volumes Anônimos:** Named Volumes explícitos (`datapolirs_frontend_node_data`, `datapolirs_frontend_next_data`, `datapolirs_postgres_data`, `datapolirs_redis_data`).
  - **Orquestrador Canônico:** `Makefile` com alvos `make up`, `make down`, `make test`.
- **Decisões Arquiteturais Vigentes (ADRs Críticas para esta Demanda):**
  - **[[ADR_010_datapolirs_Emendas_Orcamentarias_e_Legislativo_MultiFonte]]:** Centraliza a busca externa em endpoint polimórfico `/api/v1/gabinete/projetos-lei/buscar-externo` delegando para adaptadores dedicados (`AlrsAdapter`, `CamaraAdapter`, `SenadoAdapter`). O `AlrsAdapter` opera via web scraping assíncrono sobre o portal Drupal da ALRS.
  - **[[ADR_016_datapolirs_Refatoracao_Monorepo_Canonico]]:** Monorepo Simétrico (`backend/` e `frontend/`).
  - **[[ADR_020_datapolirs_Blindagem_FullStack_CI_Playwright_e_Confinamento_Loopback]]:** Testes E2E sem dependência de hosts abertos.
  - **[[ADR_026_datapolirs_Cookie_Host_Only_via_Rewrite_Same_Origin]]:** Roteamento em produção com Nginx e cookies Host-Only.

---

### 2. Doutrina Arquitetural da BIBLIOTECA (RAG Local CTDOL)
> [!quote] Fundamentos Clássicos & Diretrizes Epistêmicas
> - **Resiliência de Integração Externa (Michael Nygard — Release It!):** Serviços de terceiros e portais web falham sem aviso prévio. Todo adaptador externo deve implementar timeouts explícitos, tratamento defensivo de payloads vazios ou malformados, isolamento de falhas (a falha de uma fonte estadual não pode derrubar a busca federal) e circuit breakers / logging semântico.
> - **Engenharia de Restrição Ponytail (The 7-Rung Ladder):** Antes de propor bibliotecas pesadas de automação de browser (Selenium/Playwright) no backend para scraping, esgote os degraus 1 a 4: (1) YAGNI; (2) Reuso do cliente `httpx` assíncrono já existente; (3) Identificação de rotas de dados estruturados (APIs JSON não documentadas ou feeds XML/RSS do portal da ALRS); (4) Parsing cirúrgico com `BeautifulSoup` sem introdução de dependências acidentais.

---

### 3. Manifesto Clean Code & Quality Gates Inegociáveis
1. **SOLID & Fail-Fast:** Early Return em condicionais; proibição de blocos 'else' aninhados; interfaces e contratos de adapters explícitos.
2. **Docker Local Zero-Trust (ADR 035/036):** Confinamento estrito em `127.0.0.1`, proibição de binds em `0.0.0.0`, política `restart: "no"` e Named Volumes.
3. **Idempotência & Contratos de Dados:** Objetos retornados pelos adaptadores devem mapear estritamente para os schemas Pydantic esperados (`ProposicaoExternaSchema`), garantindo campos obrigatórios (`ementa`, `autor`, `identificador_externo`, `ano`, `url_fonte`) com fallbacks seguros para valores nulos.
4. **Validação Sanitária Obrigatória:** Passagem com zero erros nos comandos de verificação: `pytest tests/` (ou `pytest -v`), `npm run test` (Vitest), `npm run lint` e `npm run build` (Type-checking / Frontend).

---

### 4. O Problema Relatado (Bug Report de Produção)

- **URL do Incidente:** `https://datapoli.ctdol.com.br/projetos-lei`
- **Sintoma Visual:** Na aba **"BUSCAR NAS FONTES OFICIAIS"**, ao digitar o termo **`nadine`** (referente à Deputada Estadual **Delegada Nadine Anflor** — ALRS), o sistema retorna imediatamente:
  > *"Nenhuma proposição encontrada para esse nome nas fontes oficiais."*
- **Gravidade / Impacto:** O módulo legislativo é crucial para o gabinete acompanhar matérias de parlamentares estaduais do Rio Grande do Sul. Se a ALRS estiver inoperante ou quebrando silenciosamente, o usuário perde 100% da visibilidade de matérias estaduais (a Câmara e o Senado só retornarão dados para deputados federais e senadores).

---

### 5. Roteiro Operacional da Sessão: Diagnóstico e Correção da Busca Multi-Fonte

Execute com rigor as etapas sequenciais abaixo no repositório `/Users/cpinfo/Documents/datapoliRS`:

#### Etapa 1: Mapeamento de Ponta a Ponta do Fluxo de Busca
1. Inspecione o frontend em `frontend/src/app/(dashboard)/projetos-lei/page.tsx` (ou componentes associados em `frontend/src/components/legislativo/`):
   - Qual endpoint exato é acionado ao digitar na caixa de busca? (Ex: `/api/v1/gabinete/projetos-lei/buscar-externo`).
   - Quais parâmetros de query são enviados? (`autor`, `nome`, `termo`, `q`, etc.).
   - Há debounce? Como o frontend lida com loading, erros HTTP (500/502/504) e arrays vazios `[]`?
2. Inspecione o router backend em `backend/app/routers/legislative.py`:
   - Como o endpoint `/buscar-externo` recebe os parâmetros?
   - Como é feita a agregação das fontes? Se usa `asyncio.gather`, o parâmetro `return_exceptions=True` está ativo?
   - Existe algum bloco `try...except Exception:` engolindo erros e retornando `[]` silenciosamente sem logar o traceback da ALRS?

#### Etapa 2: Diagnóstico Pericial do `AlrsAdapter` (`backend/app/services/legislative_sources.py`)
1. Inspecione a classe `AlrsAdapter`:
   - Qual URL base e endpoint de pesquisa da ALRS estão configurados?
   - Como o termo de busca é injetado na URL? ("nadine" vs "Nadine" vs "Delegada Nadine" vs "Nadine Anflor"). O portal da ALRS exige maiúsculas, codificação de URL específica (ex: ISO-8859-1 vs UTF-8) ou parâmetros adicionais (ex: legislatura, ano, tipo de matéria)?
   - Como o HTML retornado pela ALRS é processado? O layout Drupal 9 mudou? As classes CSS/seletores usados para extrair ementa, número do projeto e autor ainda existem?
   - Qual `User-Agent` e cabeçalhos HTTP estão sendo enviados? O portal da ALRS está bloqueando chamadas automatizadas sem `User-Agent` de navegador (HTTP 403 Forbidden)?
   - O portal da ALRS possui certificado TLS válido ou a requisição falha por SSL?

#### Etapa 3: Reprodução Isolada e Teste Funcional (Script de Spike)
1. Crie um script temporário ou execute no terminal/Python isolado um teste direto contra a ALRS:
   ```python
   # Exemplo conceitual para testar na IDE
   import asyncio
   from app.services.legislative_sources import AlrsAdapter

   async def test():
       adapter = AlrsAdapter()
       res = await adapter.buscar_por_nome("nadine")
       print(f"Resultados com 'nadine': {len(res)}")
       res2 = await adapter.buscar_por_nome("Nadine")
       print(f"Resultados com 'Nadine': {len(res2)}")
       res3 = await adapter.buscar_por_nome("Delegada Nadine")
       print(f"Resultados com 'Delegada Nadine': {len(res3)}")

   asyncio.run(test())
   ```
2. Analise o status HTTP real retornado pelo servidor da ALRS e o conteúdo da resposta (HTML ou erro).

#### Etapa 4: Correção Estrutural e Blindagem Ponytail
1. **Se o layout ou URL da ALRS mudou:** Atualize os seletores e a URL de busca. Verifique se a ALRS oferece endpoint de dados abertos ou JSON nativo no portal antes de insistir em scraping frágil.
2. **Se o case sensitivity ou normalização de nome for a causa:** Implemente normalização no `AlrsAdapter` (ex: remoção de acentos, capitalização ou busca flexível que suporte tanto "nadine" quanto "Delegada Nadine").
3. **Se houver bloqueio WAF/User-Agent:** Adicione cabeçalhos HTTP padrão de navegador legítimo (`User-Agent: Mozilla/5.0...`).
4. **Isolamento de Falhas e Logging Semântico:**
   - Assegure que se a ALRS falhar ou der timeout, um log `logger.error` detalhado seja emitido.
   - O endpoint `/buscar-externo` deve informar de maneira transparente no payload quais fontes responderam com sucesso e quais tiveram erro temporário (ex: `fontes_com_erro: ["ALRS"]`), permitindo que o frontend exiba um aviso elegante ao usuário em vez de um falso "nenhuma proposição encontrada".

#### Etapa 5: Testes Automatizados e Homologação
1. Crie ou atualize os testes unitários em `backend/tests/` (ex: `test_legislative_sources.py` com mocks via `respx` ou `unittest.mock`) para garantir que os adaptadores da ALRS, Câmara e Senado tratem cenários de sucesso, resposta vazia e falha de rede sem quebrar.
2. Execute a suíte completa de testes:
   - Backend: `pytest backend/tests/ -v`
   - Frontend: `npm run test` (Vitest) e `npm run build`
3. Valide localmente a interface subindo os serviços (`make up`) e testando a pesquisa por "nadine" na tela `/projetos-lei`.

---

### 6. Entregável Obrigatório (Handover na Zona de Pouso)
Ao concluir sua análise e trabalho, gere um relatório técnico completo no **Padrão Ouro SLC** com a sua assinatura visual de motor:
`🟣 Claude Code (Operações Especiais)`

Salve o relatório diretamente na Zona de Pouso do cofre no seguinte caminho:
`/Users/cpinfo/Documents/COFRE_CTDOL_2026/REINO_MENTAL/01_ZONAS_DE_POUSO/OUTPUTs_CLAUDE/2026-09-15_Relatorio_Handover_DATAPOLIRS_Busca_Projetos_Lei_ALRS.md`

O relatório de handover deve conter:
- Totem Resumo Executivo (`> [!tldr]`) com a causa raiz encontrada (RCA)
- Diff técnico das correções aplicadas no backend e/ou frontend
- Evidências de testes locais (Pytest e teste funcional da busca por "nadine")
- Avaliação de conformidade com as ADRs (especialmente ADR 010 e ADR 020)
- Recomendações para deploy da release em produção via esteira CI/CD (ADR 022)

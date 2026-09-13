---
name: System Documenter
description: Sub-rotina técnica nativa para decompor bases de código em especificações Docs-as-Code. Gera diagramas C4 em Mermaid (Nível 1 Contexto e Nível 2 Contêineres), sintetiza seções críticas do arc42, formata contratos OpenAPI/REST e modelagens de banco de dados (DER/DDL).
---

# Skill: System Documenter (Gerador Docs-as-Code)

Esta skill fornece à IA os templates, padrões e atalhos técnicos para inspecionar sistemas e gerar documentações vivas e padronizadas no ecossistema CTDOL.

---

## 🛠️ Procedimento de Execução

Ao documentar ou auditar uma base de código:

### 1. Extração do Modelo C4 Integral (Mermaid & [[ADR_045_governanca_Padrao_CTDOL_Desenvolvimento_Docs_as_Code_C4_Canvas]])
- **Nível 1 (Contexto):** Mapeie os usuários/atores, o sistema central e todos os serviços externos (TSE, IBGE, Gateways de Pagamento, Keycloak).
- **Nível 2 (Contêineres):** Mapeie os processos executáveis (Frontend SPA, Backend API, Bancos Relacionais, Motores Analíticos/DuckDB, Caches e Queues) e os protocolos de comunicação (HTTPS/JSON, WSS, TCP).
- **Nível 3 (Componentes):** Mapeie a arquitetura em camadas (Controllers, Use Cases, Services, Repositories).
- **Nível 4 (Código & Classes - Nota Canônica Dedicada):**
  - Crie a nota `Diagrama_Classes_[projeto].md` em `[PROJETO]/DOC_OF-[projeto]/`.
  - Separe rigorosamente **Domínio Puro (Entidades, Value Objects, Interfaces)** de **Implementação / Infraestrutura (Serviços, Repositórios, Adapters)** baseando-se no livro *Engenharia de Software Moderna* (Marco Tulio Valente, Cap. 4).
  - Obedeça à **Regra 10.2**: orientação vertical (`direction TB`), quebras `<br/>` a cada 35-45 caracteres e sem rolagem lateral em A4.
  - No `DOC_001`, insira a transclusão nativa: `![[Diagrama_Classes_[projeto]]]`.

### 2. Geração do Obsidian Canvas Dinâmico (`.canvas`)
- Crie o arquivo `Mapa_Arquitetura_Classes_[projeto].canvas` na raiz `[PROJETO]/`.
- Utilize a especificação aberta **JSON Canvas 1.0** com nós de arquivo nativos (`"type": "file"`):
  - Nó MOC Central: `[PROJETO]/00_MOC_[PROJETO].md`
  - Nó Arquitetura Macro: `[PROJETO]/DOC_OF-[projeto]/DOC_001_Visao_Geral_e_C4_Arquitetura.md`
  - Nó Diagrama de Classes: `[PROJETO]/DOC_OF-[projeto]/Diagrama_Classes_[projeto].md`
  - Nós de ADRs Relevantes: `[PROJETO]/DOC_OF-[projeto]/ADR_...`
- Isso assegura atualização automática e em tempo real no Obsidian sem duplicação de dados.

### 3. Formatação da Seção 8 do arc42 (Cross-cutting Concepts)
- Documente explicitamente:
  - **Segurança & Auth:** Estrutura dos Tokens JWT, claims obrigatórias e validação JWKS.
  - **Multi-Tenancy:** Estratégia de segregação de dados (`tenant_id`, RLS ou schemas).
  - **Idempotência:** Tratamento de repetição em endpoints não-idempotentes (`POST`/`PATCH`).
  - **LGPD:** Dados pessoais tratados, bases legais e políticas de expurgo/anonimização.

### 4. Tabela de Contratos OpenAPI / REST
- Formate a lista de endpoints em tabela com colunas:
  `| Método | Rota | Descrição | Auth / Headers | Payload Entrada (JSON) | Respostas (Status) |`

### 5. Modelagem de Dados (DER / DDL)
- Extraia ou gere o DDL SQL formatado com tipos nativos, chaves primárias UUID, índices espaciais (GIST no PostGIS) e chaves estrangeiras.

---

## 🔗 Fluxos e Decisões Integradas
- [[ADR_045_governanca_Padrao_CTDOL_Desenvolvimento_Docs_as_Code_C4_Canvas]]
- [[Fluxo_006_Arquitetura_Alta_Complexidade]]
- [[Fluxo_008_Agente_Documentador_Sistemas]]
- [[Fluxo_013_Comissionamento_Sistemas_e_Analise_Legado]]

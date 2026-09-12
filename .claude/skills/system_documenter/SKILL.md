---
name: System Documenter
description: Sub-rotina técnica nativa para decompor bases de código em especificações Docs-as-Code. Gera diagramas C4 em Mermaid (Nível 1 Contexto e Nível 2 Contêineres), sintetiza seções críticas do arc42, formata contratos OpenAPI/REST e modelagens de banco de dados (DER/DDL).
---

# Skill: System Documenter (Gerador Docs-as-Code)

Esta skill fornece à IA os templates, padrões e atalhos técnicos para inspecionar sistemas e gerar documentações vivas e padronizadas no ecossistema CTDOL.

---

## 🛠️ Procedimento de Execução

Ao documentar ou auditar uma base de código:

### 1. Extração do Modelo C4 (Mermaid)
- **Nível 1 (Contexto):** Mapeie os usuários/atores, o sistema central e todos os serviços externos (TSE, IBGE, Gateways de Pagamento, Keycloak).
- **Nível 2 (Contêineres):** Mapeie os processos executáveis (Frontend SPA, Backend API, Bancos Relacionais, Motores Analíticos/DuckDB, Caches e Queues) e os protocolos de comunicação (HTTPS/JSON, WSS, TCP).

### 2. Formatação da Seção 8 do arc42 (Cross-cutting Concepts)
- Documente explicitamente:
  - **Segurança & Auth:** Estrutura dos Tokens JWT, claims obrigatórias e validação JWKS.
  - **Multi-Tenancy:** Estratégia de segregação de dados (`tenant_id`, RLS ou schemas).
  - **Idempotência:** Tratamento de repetição em endpoints não-idempotentes (`POST`/`PATCH`).
  - **LGPD:** Dados pessoais tratados, bases legais e políticas de expurgo/anonimização.

### 3. Tabela de Contratos OpenAPI / REST
- Formate a lista de endpoints em tabela com colunas:
  `| Método | Rota | Descrição | Auth / Headers | Payload Entrada (JSON) | Respostas (Status) |`

### 4. Modelagem de Dados (DER / DDL)
- Extraia ou gere o DDL SQL formatado com tipos nativos, chaves primárias UUID, índices espaciais (GIST no PostGIS) e chaves estrangeiras.

---

## 🔗 Fluxos Integrados
- [[Fluxo_006_Arquitetura_Alta_Complexidade]]
- [[Fluxo_008_Agente_Documentador_Sistemas]]

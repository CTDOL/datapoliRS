---
name: Code Conciliator
description: Sub-rotina técnica nativa para conciliação e anti-drift de arquitetura. Compara o código-fonte real e relatórios de IDEs externas com os planos de integração originais (Fluxo 006) e diretrizes de mentoria (Fluxo 007), identificando discrepâncias para o Fluxo 008.
---

# Skill: Code Conciliator (Anti-Drift & Sincronização SSoT)

Esta skill fornece à IA a inteligência de conciliação para detectar discrepâncias entre o que foi planejado na arquitetura e o que foi efetivamente construído nas IDEs externas.

---

## 🛠️ Procedimento de Execução

Ao receber código-fonte ou relatórios de IDEs externas (Cursor, Cline, Aider, terminal):

### 1. Triagem de Linha de Base (Baseline Comparison)
- Localize o plano arquitetural original em `REINO_MENTAL/02_CADERNO_DO_DEV/` (gerado pelo [[Fluxo_006_Arquitetura_Alta_Complexidade]]) ou as ADRs vigentes do projeto.
- Verifique se as diretrizes de código limpo do [[Fluxo_007_Mentoria_Externa]] foram respeitadas.

### 2. Detecção de Tipos de Drift
Classifique as divergências encontradas em 3 categorias:
- **Code Drift:** Rotas de API, middlewares ou componentes que foram criados de forma diferente da especificação original.
- **Data Drift:** Alterações nas colunas, tipos de dados, chaves estrangeiras ou migrações em relação ao DER/DDL planejado.
- **Decision Drift:** Decisões de contorno ou atalhos técnicos adotados pelo desenvolvedor durante a sessão de codificação que demandam uma nova ADR formal.

### 3. Síntese de Conciliação
- Estruture um resumo executivo de divergências destacando:
  - O que foi implementado conforme o plano.
  - O que divergiu e por quê.
  - As novas ADRs que precisam ser geradas para manter o cofre como a SSoT real de produção.

---

## 🔗 Fluxos Integrados
- [[Fluxo_006_Arquitetura_Alta_Complexidade]]
- [[Fluxo_007_Mentoria_Externa]]
- [[Fluxo_008_Agente_Documentador_Sistemas]]

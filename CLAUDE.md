# Âncora de Governança e Subordinação à SSoT — CTDOL (Claude Code)

> [!tldr] Diretriz Constitucional do Claude Code (Operações Especiais)
> - **Projeto:** DATAPOLIRS
> - **SSoT Central:** `/Users/cpinfo/Documents/COFRE_CTDOL_2026` (Regime: **LEITURA EXCLUSIVA / Read-Only**)
> - **Zona de Pouso de Handover:** `/Users/cpinfo/Documents/COFRE_CTDOL_2026/REINO_MENTAL/01_ZONAS_DE_POUSO/OUTPUTs_CLAUDE`
> - **Motor & Assinatura:** `🟣 Claude Code (Operações Especiais)`

## 1. Autoridade Arquitetural e Primazia da SSoT
1. **Fonte Única de Verdade:** Todas as decisões canônicas, arquiteturas e ADRs residem no Cofre CTDOL em `/Users/cpinfo/Documents/COFRE_CTDOL_2026/DATAPOLIRS/`.
2. **Subordinação:** Este repositório de código deve operar em estrita conformidade com as ADRs catalogadas no cofre. Qualquer divergência deve ser sinalizada como Drift.
3. **Regime de Acesso ao Cofre (Read-Only):** Este repositório possui acesso de LEITURA ao Cofre (`/Users/cpinfo/Documents/COFRE_CTDOL_2026`). A IA pode e deve ler notas, ADRs, diagramas C4 e documentações no cofre para obter contexto e regras de negócio. É expressamente proibido alterar, criar ou deletar arquivos dentro do cofre a partir deste repositório (com exceção exclusiva do envio do relatório de handover e quality gate na pasta designada `OUTPUTs_CLAUDE/`). Todo o desenvolvimento é estritamente local neste workspace.
4. **Configuração do Acesso (local, não versionada):** O acesso ao cofre está liberado em `permissions.additionalDirectories` do `.claude/settings.json`. Esse arquivo é ignorado pelo `.gitignore` e vale só nesta máquina; em outro clone, o cofre precisa ser adicionado manualmente. A configuração libera leitura **e** escrita: o regime Read-Only do item 3 é garantido apenas por esta regra, sem trava técnica (`deny`). Operações git no cofre (`add`, `commit`, `push`) também são vedadas a partir deste repositório.

## 2. Vedação Absoluta de Commits e Push Autônomos (Regra 7.5)
- É **TERMINANTEMENTE PROIBIDO** à IA disparar `git commit` ou `git push` por iniciativa própria ou por presunção de fechamento de tarefa.
- Commits e pushes pertencem exclusivamente à ordem nominal expressa do operador humano na sessão.
- Mensagens de commit sugeridas devem seguir a rastreabilidade da Federação Paritária: título com tag `[Claude Code]`, referência `Refs #NN` (nunca `Closes #NN`) e `Co-authored-by: Claude Code <claude@anthropic.com>`.

## 3. Governança Docker & Confinamento Local (Zero-Trust — ADR 035/036)
- **Localhost Only:** Todos os binds de portas devem apontar estritamente para `127.0.0.1`. Binds abertos (`0.0.0.0`) são terminantemente proibidos.
- **Boot Política:** `restart: "no"` obrigatório no compose de desenvolvimento.
- **Named Volumes:** Volumes de dependências (`node_modules`, `.next`) e dados persistentes (`datapolirs_postgres_data`, `datapolirs_redis_data`) devem utilizar volumes nomeados para evitar contaminação do host.

## 4. Doutrina Canônica de Evolução de Banco de Dados (Regra 12.2 / Fowler & Sadalage)
- **Todas as Mudanças são Migrações:** Toda alteração de schema ou dados deve nascer como script de migração versionado no repositório com o código (Alembic). DDL/DML manual em console de produção é estritamente proibido.
- **Instâncias Locais Isoladas:** Desenvolva e teste estritamente contra banco local isolado em Docker (`restart: "no"`).
- **Padrão Expand/Contract para Zero-Downtime:** Mudanças destrutivas de schema em produção devem ser fatiadas em 3 fases (Expand com escrita dupla -> Transition -> Contract) para garantir compatibilidade retroativa e sustentação de múltiplas versões concorrentes.
- **Validação em CI/CD:** Testes de integração devem aplicar a cadeia completa de migrações em contêiner efêmero a partir do zero.

## 5. Consulta Ativa à Doutrina da BIBLIOTECA (RAG Local)
Durante a sessão, caso surja dúvida sobre padrões de projeto, arquitetura de software ou Clean Code, você pode consultar o RAG Local do cofre diretamente via CLI:
```bash
python3 "/Users/cpinfo/Documents/COFRE_CTDOL_2026/.agents/skills/rag_local/scripts/rag_engine.py" search "<sua_duvida_arquitetural>" --top-k 3
```

## 6. Entrega Obrigatória de Handover
Ao finalizar sessões de desenvolvimento, diagnóstico ou refatoração, a IA DEVE gerar o relatório técnico no padrão Padrão Ouro SLC e salvá-lo diretamente em:
`/Users/cpinfo/Documents/COFRE_CTDOL_2026/REINO_MENTAL/01_ZONAS_DE_POUSO/OUTPUTs_CLAUDE/YYYY-MM-DD_Relatorio_Handover_DATAPOLIRS_[Tema].md`

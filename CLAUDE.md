# Âncora de Governança e Subordinação à SSoT — CTDOL

> [!tldr] Diretriz Constitucional do Claude Code (Operações Especiais)
> - **Projeto:** DATAPOLIRS
> - **SSoT Central:** `/Users/cpinfo/Documents/COFRE_CTDOL_2026`
> - **Zona de Pouso de Handover:** `/Users/cpinfo/Documents/COFRE_CTDOL_2026/REINO_MENTAL/01_ZONAS_DE_POUSO/OUTPUTs_CLAUDE`
> - **Motor & Assinatura:** `🟣 Claude Code (Operações Especiais)`

## 1. Autoridade Arquitetural e Primazia da SSoT
1. **Fonte Única de Verdade:** Todas as decisões canônicas, arquiteturas e ADRs residem no Cofre CTDOL em `/Users/cpinfo/Documents/COFRE_CTDOL_2026/DATAPOLIRS/`.
2. **Subordinação:** Este repositório de código deve operar em estrita conformidade com as ADRs catalogadas no cofre. Qualquer divergência deve ser sinalizada como Drift.

## 2. Governança Docker & Confinamento Local (Zero-Trust)
- **Localhost Only:** Todos os binds de portas devem apontar estritamente para `127.0.0.1`. Binds abertos (`0.0.0.0`) são terminantemente proibidos.
- **Boot Política:** `restart: "no"` obrigatório no compose de desenvolvimento.
- **Named Volumes:** Volumes de dependências (`node_modules`, `.next`) devem utilizar volumes nomeados para evitar contaminação do host.

## 3. Consulta Ativa à Doutrina da BIBLIOTECA (RAG Local)
Durante a sessão, caso surja dúvida sobre padrões de projeto, arquitetura de software ou Clean Code, você pode consultar o RAG Local do cofre diretamente via CLI:
```bash
python3 "/Users/cpinfo/Documents/COFRE_CTDOL_2026/.agents/skills/rag_local/scripts/rag_engine.py" search "<sua_duvida_arquitetural>" --top-k 3
```

## 4. Entrega Obrigatória de Handover
Ao finalizar sessões de desenvolvimento, diagnóstico ou refatoração, o Claude Code DEVE gerar o relatório técnico no padrão Padrão Ouro SLC e salvá-lo diretamente em:
`/Users/cpinfo/Documents/COFRE_CTDOL_2026/REINO_MENTAL/01_ZONAS_DE_POUSO/OUTPUTs_CLAUDE/YYYY-MM-DD_Relatorio_Handover_DATAPOLIRS_[Tema].md`

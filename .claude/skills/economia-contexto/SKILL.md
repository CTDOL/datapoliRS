---
name: economia-contexto
description: Reduzir o ruído e o custo de tokens de uma sessão de Claude Code num projeto — enxugar CLAUDE.md inchado, configurar .claudeignore, decidir quando incluir arquivo específico em vez de deixar o Claude explorar sozinho, e saber quando vale rodar /compact. Use quando o usuário reclamar que a sessão está lenta, cara, ou "gastando muito token", quando o CLAUDE.md do projeto passar de umas 200 linhas, quando o Claude estiver lendo arquivo grande ou irrelevante repetidamente, ou quando o usuário pedir para "otimizar o contexto" ou "deixar isso mais leve". Também use proativamente ao criar um CLAUDE.md novo para um projeto grande, para já nascer enxuto em vez de crescer sem controle depois.
---

# Economia de contexto

## O problema, com precisão

Contexto gasto à toa não é neutro — ele desloca contexto que poderia estar sendo usado para pensar sobre o problema real. Um `CLAUDE.md` de 800 linhas carregado toda sessão, ou um Claude que lê `vendor/` inteiro procurando uma função, é a mesma categoria de erro: informação de baixo valor ocupando o lugar de informação de alto valor.

Três frentes resolvem a maior parte disso, cada uma ataca um tipo diferente de desperdício:

1. **`CLAUDE.md` enxuto** — evita carregar informação irrelevante *toda sessão*, mesmo quando não é usada.
2. **`.claudeignore`** — evita que o Claude sequer veja arquivos que nunca deveria ler (segredos, builds, dependências).
3. **Inclusão direcionada + `/compact`** — evita acumular, *dentro* de uma sessão já em andamento, leitura e histórico que não serve mais.

## Frente 1 — CLAUDE.md enxuto

Um `CLAUDE.md` bom cabe na cabeça: comandos de build/test, convenções que não são óbvias pelo código, e regras de segurança. Tudo que é "bom saber mas raramente necessário" é candidato a sair.

**Como enxugar um CLAUDE.md existente:**

1. Releia linha por linha e classifique cada uma em três baldes:
   - **Essencial** — necessário em toda sessão (comando de build, de teste, regra de segurança inegociável)
   - **Referência** — só importa em contexto específico (arquitetura detalhada, troubleshooting de caso raro, guia de uma área do código)
   - **Redundante** — duplica o que já está em outro doc, ou é verboso sem ganho
2. Balde **Referência** vira arquivo separado (`docs/arquitetura.md`, `docs/troubleshooting.md`) e no `CLAUDE.md` fica só uma **sinopse rica + link**: 3-5 frases com detalhe concreto (nomes, comandos, limiares), não um link pelado. Isso importa porque o Claude precisa conseguir responder a maioria das perguntas só com a sinopse — o link é para o caso raro que precisa do detalhe completo.
3. Balde **Redundante** simplesmente sai.
4. **Nunca corte sem aprovação.** Mostre o plano de categorização antes de mexer, e confira que nada de essencial (regra de segurança, comando que quebra se errado) foi parar no balde errado.

**Meta prática, não regra rígida:** projetos médios ficam bem com `CLAUDE.md` abaixo de 200 linhas. Projeto muito grande com múltiplos serviços pode justificar mais, mas aí a estrutura em sub-documentos importa ainda mais.

## Frente 2 — .claudeignore

`.claudeignore` funciona como `.gitignore`, mas para o que o Claude Code varre e pode ler. Objetivo: tirar do caminho o que nunca precisa ser lido, para busca e listagem de arquivo não perderem tempo (e tokens) nisso.

```
# .claudeignore — ponto de partida, ajuste por stack
node_modules/
vendor/
dist/
build/
.venv/
*.min.js
*.lock
coverage/
.git/
*.log
# dumps e backups — nunca devem ser lidos por engano
*.sql
*.sqlite
*.tar.gz
*.zip
```

**Regra de ouro:** se um arquivo nunca precisa ser lido para entender ou modificar o sistema — porque é gerado, é dependência de terceiro, ou é dado — ele vai para o `.claudeignore`. Segredo (`.env`) já deveria estar no `.gitignore`; coloque também aqui por camada extra, mas a proteção real de segredo é nunca commitá-lo, não esconder do Claude.

## Frente 3 — Inclusão direcionada e /compact

Dentro de uma sessão já rodando, dois hábitos cortam desperdício sem precisar de configuração nova:

- **Aponte o arquivo em vez de pedir para explorar.** "Olha o `services/pagamento.php`" é mais barato que "onde fica a lógica de pagamento" quando você já sabe o caminho — a segunda opção faz o Claude gastar buscas para achar o que você já sabia.
- **`/compact` quando a sessão muda de fase, não quando está lenta.** O momento certo é a transição — terminou de investigar e vai começar a implementar, terminou uma feature e vai começar outra — não "está demorando", que é sintoma tardio. Comprimir no meio de uma investigação ainda ativa arrisca perder o fio do que já foi descoberto.

## Como isso se conecta com o resto do repo

- `mapa-rapido` gera o primeiro entendimento do projeto; o resultado dele (pontos de entrada, onde não mexer) é exatamente o tipo de conteúdo que deveria virar `CLAUDE.md` essencial, não ficar solto na conversa.
- `diagnostico-ambiente` e `analise-legado` produzem achados detalhados que tendem a ser longos — esses são candidatos naturais a `references/` ou a doc separado com sinopse no `CLAUDE.md`, não para colar inteiros nele.

## Quando NÃO aplicar

- Projeto pequeno, sessão curta, `CLAUDE.md` já com menos de 100 linhas — não há problema para resolver. Aplicar isso por reflexo em projeto pequeno é o mesmo erro de arquitetar CRUD sem regra: cerimônia sem ganho.
- Se o pedido for sobre performance da aplicação em si (não da sessão do Claude), isso não é economia de contexto — é outro problema.

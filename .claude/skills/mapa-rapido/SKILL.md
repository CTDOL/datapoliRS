---
name: mapa-rapido
description: Gerar rapidamente um mapa de orientação de um projeto desconhecido ou pouco familiar — o que é, como roda, onde entrar, onde não mexer sem cuidado — logo no início de uma sessão nova, sem precisar de uma investigação completa. Use sempre que o usuário abrir um repositório que o Claude ainda não viu e pedir algo como "me situa nesse projeto", "por onde eu começo", "o que esse repositório faz", ou quando a primeira tarefa pedida (corrigir algo, adicionar algo) exigir entender a estrutura antes, e ainda não existir um mapa salvo. Também dispara quando o usuário disser que está perdido no próprio código ou que "ninguém documentou isso". Mais leve que `analise-legado` — não extrai regra de negócio nem propõe refatoração, só orienta rápido. Se a tarefa pedir investigação profunda de bug ou decisão de refatorar, use `analise-legado` em vez desta.
---

# Mapa rápido de projeto

## Por que isso existe, separado de `analise-legado`

`analise-legado` é uma investigação completa — extrai regra de negócio, propõe refatoração, tem 5 fases. Ela é cara demais para a primeira coisa que você faz ao abrir uma pasta nova. A maioria das sessões só precisa de uma resposta rápida a "onde eu tô e como não quebro nada" antes de seguir para a tarefa real que o usuário pediu.

Esta skill é o degrau anterior: 5-10 minutos de leitura guiada, não uma investigação. Se no meio do mapeamento aparecer sinal de que o projeto precisa de investigação de verdade (regra de negócio confusa, comportamento que ninguém explica), pare e sugira `analise-legado` em vez de continuar por conta própria.

## Passo 1 — Rodar o inventário técnico

```bash
../arquitetura-hexagonal/scripts/detect-stack.sh /caminho/do/projeto
```

Isso já responde: que stack, se tem Git, se tem teste, tamanho, sinais de acoplamento. Não repita esse trabalho manualmente — leia a saída do script antes de abrir qualquer arquivo.

## Passo 2 — Achar os pontos de entrada, não o projeto inteiro

O objetivo não é ler tudo. É achar rápido:

1. **Como alguém roda isso localmente** — `README.md`, `package.json` (scripts), `Makefile`, `docker-compose.yml`, `manage.py`. Se nenhum existir, é o primeiro achado a reportar: projeto sem instrução de como rodar.
2. **Por onde a execução começa** — `index.php`, `main.py`, `routes/`, `app.js`, o controller de entrada. Em uma stack web, normalmente é o roteador ou o arquivo que registra as rotas.
3. **Onde fica o estado** — schema de banco, migrations, ou (se não tiver banco) onde os dados vivem. Nome de tabela e coluna já entrega vocabulário de negócio, mesmo sem ler uma linha de lógica.
4. **O que já está testado** — pasta de teste, se existir. Área sem teste é área onde qualquer mudança sua precisa de mais cautela.

Essa é a mesma ordem de leitura da Fase 1 de `analise-legado`, só que você para aqui em vez de seguir para extrair regras.

## Passo 3 — Escrever o mapa, não guardar na cabeça

Produza um arquivo curto — sugestão de nome `MAPA.md` na raiz do projeto, ou só a resposta no chat se o usuário não pediu para salvar. Use este formato:

```markdown
# Mapa rápido — <nome do projeto>

## O que é
<uma frase, em linguagem de negócio, não técnica>

## Stack
<resumo da saída do detect-stack.sh>

## Como rodar localmente
<comando(s), ou "não documentado — perguntar ao usuário">

## Por onde entra
<arquivo/rota de entrada principal>

## Onde não mexer sem confirmar antes
<arquivos grandes, sem teste, ou com sinal de acoplamento — apontados pelo detect-stack.sh>

## O que eu não sei e preciso perguntar
<lacunas reais — não invente resposta aqui>
```

A última seção é a que mais importa e a mais fácil de pular por pressa. Nunca preencha "por onde entra" ou "o que faz" com suposição — se o `detect-stack.sh` e uma checagem rápida dos arquivos não deixarem claro, escreva a pergunta em vez do palpite.

## Quando isso não é suficiente

Se durante o mapeamento você perceber que o projeto tem lógica de negócio densa, comportamento estranho sem explicação, ou o usuário descrever o código como "bagunça"/"gambiarra": pare aqui e sugira `analise-legado` — essa skill vai fundo em regra de negócio, teste de caracterização e plano de refatoração, que este mapa rápido não tenta fazer.

Se o pedido já vier claro (usuário sabe exatamente o que quer mudar e onde), pule esta skill — ela existe para orientação inicial, não para toda tarefa.

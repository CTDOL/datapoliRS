---
name: analise-legado
description: Analisar um sistema que já existe, extrair a regra de negócio que está enterrada nele, diagnosticar problemas e propor refatoração incremental sem quebrar comportamento. Use quando o pedido for entender código herdado ou antigo, descobrir "o que esse sistema faz", investigar um bug em código desconhecido, avaliar se vale refatorar ou reescrever, ou quando o usuário descrever o próprio código como bagunça, gambiarra ou Frankenstein. Cobre teste de caracterização e strangler fig. Qualquer stack.
---

# Análise de sistema existente

## Postura

Código que funciona há anos acumulou conhecimento que ninguém documentou. Cada gambiarra costuma ser a cicatriz de um caso real. **Antes de julgar, entenda por que está assim** — e principalmente: nunca apague uma condição estranha sem descobrir que caso ela cobre.

Ao mesmo tempo, "funciona" não é o mesmo que "é seguro mexer". A diferença entre os dois é ter teste.

## Fase 0 — Rede de segurança (não pule)

Antes de qualquer edição:

```bash
scripts/snapshot.sh /caminho/do/projeto
```

Ele cria um tar.gz datado e, se não houver Git, inicializa o repositório com um commit do estado atual. Isso não é sobre risco de produção — é sobre **poder comparar depois** e voltar sem perder a tarde.

Sem esse ponto de referência você não consegue provar que a refatoração preservou o comportamento.

## Fase 1 — Mapear antes de opinar

```bash
../arquitetura-hexagonal/scripts/detect-stack.sh /caminho/do/projeto
```

Depois, leia nesta ordem — é a ordem que revela o negócio mais rápido:

1. **Ponto de entrada** (`index.php`, `routes/`, `main.py`) — mostra tudo que o sistema faz
2. **Schema do banco** — as tabelas e colunas são o modelo de domínio real, mesmo que ninguém tenha chamado assim. Nomes de colunas revelam o vocabulário do negócio.
3. **Os 5 maiores arquivos** — é onde a regra está enterrada
4. **Condicionais com comentário** — `// não remover`, `// gambiarra do caso X` são requisitos não documentados
5. **Git log, se houver** — arquivo que muda com frequência é o que dói

## Fase 2 — Extrair a regra de negócio

Este é o entregável mais valioso da análise, mais do que qualquer diagrama.

Produza uma lista assim, **em português, sem jargão técnico**:

```
REGRAS ENCONTRADAS

R1. Protocolo urgente vence em 24h; ordinário em 120h.
    Onde: index.php:88-95 (dentro de um if aninhado)
    Confiança: alta — valores literais, explícitos

R2. Se o setor for 'DTIC', pula a aprovação do chefe.
    Onde: salvar.php:203
    Confiança: média — parece regra de negócio, mas pode ter sido
    contorno temporário. CONFIRMAR COM O USUÁRIO.

R3. Datas antes de 2019 são tratadas como 2019.
    Onde: relatorio.php:47
    Confiança: baixa — provável correção de migração de dados.
    Se for isso, é lixo a remover, não regra.
```

**Sempre marque a confiança e sempre separe "regra de negócio" de "correção de bug antigo".** Refatorar tratando lixo como requisito perpetua o lixo; tratar requisito como lixo quebra o sistema. Quando a diferença não for clara no código, **pergunte** — o usuário sabe coisas que o código não conta.

## Fase 3 — Teste de caracterização

Antes de mudar qualquer estrutura, escreva um teste que **congela o comportamento atual, incluindo o que está errado**.

Não é teste de correção. É um sensor: se a refatoração mudar algo, ele avisa.

```php
// Este teste documenta o comportamento ATUAL, não o desejado.
public function test_protocolo_urgente_recebe_24h() {
    $r = calcularPrazo('urgente');
    $this->assertSame(24, $r);
}

public function test_tipo_desconhecido_devolve_zero() {
    // Provavelmente um bug. Congelado de propósito:
    // corrigir depois, num commit separado, com o usuário ciente.
    $this->assertSame(0, calcularPrazo('inexistente'));
}
```

Quando o código é impossível de testar (tudo global, tudo acoplado), use **teste de aproximação**: rode a função com N entradas, grave todas as saídas num arquivo, e compare esse arquivo antes e depois. Feio, e funciona.

Detalhes e táticas para código intestável em `references/testes-caracterizacao.md`.

## Fase 4 — Diagnóstico

Classifique cada achado em três baldes, e **seja explícito sobre qual é qual**:

| Balde | Critério | Ação |
|---|---|---|
| **Quebrado** | Produz resultado errado ou falha | Corrigir — commit próprio, isolado |
| **Arriscado** | Funciona, mas expõe a falha (SQL injection, credencial no código, sem validação) | Corrigir cedo, mesmo que feio por dentro |
| **Feio** | Funciona e é seguro, só é difícil de ler | Refatorar **só se você for mexer ali** |

O terceiro balde é o que consome mais tempo com menor retorno. Código feio, estável e que ninguém toca pode ficar feio. **Refatore o que você vai precisar mudar.**

## Fase 5 — Propor, em ordem de risco crescente

Sempre nesta sequência, nunca tudo junto:

1. **Segurança primeiro** — credencial exposta, query concatenada. Não depende de arquitetura.
2. **Separar apresentação** — tirar HTML de dentro da lógica. Risco baixo, ganho alto de leitura.
3. **Extrair persistência** — juntar SQL num repositório.
4. **Extrair caso de uso** — o que sobrou entre entrada e saída.
5. **Modelar domínio** — só agora entidades e VOs, e só onde há regra de verdade.

Cada passo é um commit, com o teste de caracterização passando entre eles. Se o passo 3 quebrou, você sabe exatamente o que reverter.

## Refatorar ou reescrever?

Pergunta que aparece sempre. Resposta honesta, e quase sempre a mesma: **refatorar**.

Reescrita parece mais rápida porque você conhece o problema novo e esqueceu do velho. Mas o sistema antigo contém anos de casos de borda que ninguém lembra, e a reescrita os redescobre um a um, em produção.

Reescrever se justifica quando: a stack não tem mais suporte, ou o sistema é pequeno o bastante para caber numa cabeça, ou você tem a lista completa de regras extraída (Fase 2) e ela é curta.

Se for reescrever, **strangler fig**: novo e velho convivem, você migra uma rota por vez atrás de uma fachada. Ver `references/strangler-fig.md`.

## O que perguntar ao usuário

Nunca invente resposta para estas — o código não contém:

- Esse comportamento estranho é regra ou é remendo? (a mais importante)
- Quem usa isso hoje, e com que frequência?
- Existe alguma parte que você já sabe que está errada e conviveu?
- Você vai precisar mexer nessa área nos próximos meses?

A última decide o quanto vale refatorar. Código estável que ninguém vai tocar não precisa de arquitetura.

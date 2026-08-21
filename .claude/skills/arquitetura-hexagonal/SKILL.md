---
name: arquitetura-hexagonal
description: Estruturar ou reestruturar um sistema isolando a regra de negócio da stack, usando portas e adaptadores (hexagonal), SOLID e DDD tático. Use quando o pedido envolver desenhar um módulo novo, decidir onde colocar uma lógica, escolher entre frameworks, separar camadas, criar entidades/casos de uso/repositórios, ou quando o usuário perguntar "onde isso deveria ficar" e "como faço isso não depender do framework". Serve para qualquer stack — PHP puro, Laravel, Node, Python, Oracle APEX, HTML estático com backend fino.
---

# Arquitetura hexagonal aplicada

## Princípio único

A regra de negócio não sabe onde está rodando. Não sabe que existe HTTP, que existe MySQL, que existe Laravel, que existe Oracle. Se você trocar tudo isso, a regra continua igual e os testes dela continuam passando.

Tudo neste documento é consequência disso.

## Antes de propor qualquer estrutura

Rode `scripts/detect-stack.sh` no diretório do projeto. Ele responde:
- que stack é (ou se são várias)
- se está em git
- se existe teste
- qual o tamanho e a idade do código

**Não proponha estrutura antes de saber isso.** Um projeto de 300 linhas em PHP puro e um Laravel de 40 mil linhas pedem respostas diferentes, e a resposta errada é pior que nenhuma.

## As três zonas

```
        ┌─────────────────────────────────────────┐
        │  ADAPTADORES DE ENTRADA                 │
        │  controller HTTP, CLI, cron, form POST, │
        │  página APEX, webhook                   │
        └───────────────────┬─────────────────────┘
                            │ chama
        ┌───────────────────▼─────────────────────┐
        │  NÚCLEO                                 │
        │                                         │
        │  casos de uso  ──►  domínio             │
        │  (orquestram)       (entidades, VOs,    │
        │                      regras invariantes)│
        │                                         │
        │  define PORTAS (interfaces) para o que  │
        │  precisa do mundo externo               │
        └───────────────────┬─────────────────────┘
                            │ implementadas por
        ┌───────────────────▼─────────────────────┐
        │  ADAPTADORES DE SAÍDA                   │
        │  repositório MySQL, cliente SMTP,       │
        │  API externa, sistema de arquivos       │
        └─────────────────────────────────────────┘
```

**Regra de dependência:** setas só apontam para dentro. O núcleo nunca importa nada de adaptador. Se você viu `use Illuminate\...` dentro de uma entidade, a arquitetura já quebrou.

## O teste de fumaça

Faça estas três perguntas em qualquer código que você for avaliar ou escrever:

1. **Consigo testar a regra sem subir banco, sem subir servidor, sem rede?** Se não, a regra está grudada num adaptador.
2. **Se eu trocar o framework, quantos arquivos mudam?** Se a resposta incluir arquivos de domínio, o framework vazou pra dentro.
3. **Um analista de negócio leria os nomes das classes e reconheceria o processo dele?** Se está tudo `Manager`, `Helper`, `Util`, `Service`, o domínio não foi modelado — foi só empilhado.

Se as três passam, a estrutura está boa mesmo que a pasta esteja com nome estranho. Se falham, mexer no nome das pastas não resolve.

## Portas: o conceito que faz o resto funcionar

Uma porta é uma **interface declarada pelo núcleo**, descrevendo o que ele precisa — em vocabulário de negócio, não de tecnologia.

Certo:
```
interface RepositorioDeProtocolos {
    função buscarPorNumero(numero): Protocolo | nulo
    função salvar(protocolo): void
    função listarPendentesDe(setor): lista de Protocolo
}
```

Errado (a tecnologia vazou para o nome e para a assinatura):
```
interface ProtocoloMySQLDAO {
    função executeQuery(sql): ResultSet
    função getConnection(): PDO
}
```

A segunda versão amarra o núcleo ao SQL. A primeira você implementa hoje com PDO, amanhã com Eloquent, depois com um arquivo JSON durante os testes — e o núcleo não percebe.

**Adaptadores implementam portas. Portas pertencem ao núcleo.** Se a interface está no mesmo pacote da implementação, ela não é uma porta, é só uma interface.

## SOLID como consequência, não como checklist

Os cinco princípios não são regras separadas para decorar. Quatro deles caem naturalmente quando você respeita a regra de dependência, e um é a base de tudo:

- **D (inversão de dependência)** — é a porta. É o princípio que sustenta o hexágono inteiro. Os outros quatro são refinamentos internos.
- **S (responsabilidade única)** — "uma razão para mudar". Um caso de uso muda quando o processo de negócio muda. Um adaptador muda quando a tecnologia muda. Se um arquivo muda pelos dois motivos, ele está atravessando a fronteira.
- **O (aberto/fechado)** — adicionar um adaptador novo não deve exigir editar o núcleo. Se exige, tem um `if` sobre tipo de tecnologia dentro do domínio.
- **L (substituição de Liskov)** — qualquer implementação de uma porta tem que servir sem o caso de uso saber qual é. Se o caso de uso precisa checar "se for o repositório X, faz diferente", a porta está mal desenhada.
- **I (segregação de interfaces)** — porta gorda obriga adaptador a implementar método que não usa. Prefira duas portas pequenas a uma grande.

Para violações concretas com correção lado a lado, veja `references/solid-exemplos.md`.

## DDD: use o tático, adie o estratégico

**DDD tático** é o vocabulário do núcleo — entidade, value object, agregado, evento de domínio, repositório. Vale em qualquer projeto que tenha regra de negócio de verdade. Detalhes em `references/ddd-tatico.md`.

O ponto que mais rende na prática: **value object**. A maioria das bugs de validação em sistema pequeno some quando você para de passar `string` e passa `CPF`, `Matricula`, `NumeroDeProtocolo` — tipos que não conseguem existir em estado inválido.

**DDD estratégico** — bounded contexts, linguagem ubíqua, context map, camada anticorrupção — só se paga quando há mais de um domínio disputando o mesmo vocabulário, ou mais de um time. Num sistema de um desenvolvedor só, ele vira cerimônia. Carregue `references/ddd-estrategico.md` **apenas** quando o problema apresentar de fato dois significados conflitantes para a mesma palavra, ou integração com sistema de terceiro.

## Como isso vira pasta, por stack

O hexágono é conceitual. A tradução para diretórios muda por stack e não deve brigar com a convenção do framework. `references/adaptadores-por-stack.md` traz o mapeamento para PHP puro, Laravel, Node/Express, Python/FastAPI, Oracle APEX e front estático.

Regra geral: **não force uma estrutura de pastas exótica dentro de um framework opinativo.** Em Laravel, ponha o núcleo em `app/Dominio` e deixe `app/Http`, `app/Models` sendo adaptadores. Brigar com o framework custa mais do que ganha.

## Quando NÃO aplicar

Diga isso ao usuário em vez de aplicar por reflexo:

- **CRUD sem regra.** Se a operação é gravar o formulário no banco sem nenhuma decisão, o hexágono adiciona três arquivos para não proteger nada. Um controller que fala com o banco está certo ali.
- **Script utilitário, one-off, protótipo descartável.** Não arquitete o que vai morrer semana que vem.
- **Sistema pequeno que funciona e ninguém vai mexer.** "Funciona e está parado" é um estado válido.

A pergunta que decide: **essa regra vai mudar, e alguém vai precisar entender ela depois?** Se as duas forem sim, isola. Se alguma for não, deixa simples.

## Roteiro ao aplicar num pedido

1. Rode `detect-stack.sh`.
2. Identifique **a regra de negócio** no pedido — não a tela, não a tabela. Se o usuário só descreveu tela e tabela, pergunte qual decisão o sistema toma.
3. Nomeie as entidades e value objects com as palavras do domínio dele.
4. Declare as portas necessárias.
5. Só então escolha onde cada arquivo vai, conforme a stack.
6. Escreva o teste do caso de uso **sem banco** — se não conseguir, volte ao passo 4.

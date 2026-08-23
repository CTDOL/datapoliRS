# O mesmo hexágono em cada stack

O núcleo é idêntico em todas. Só muda o que é adaptador e onde o framework espera os arquivos.

**Regra que vale para todas:** não brigue com a convenção do framework. Coloque o núcleo num diretório próprio e deixe as pastas nativas serem a casca.

---

## PHP puro / procedural (o caso Frankenstein)

Ponto de partida típico: `index.php` com HTML, SQL e regra no mesmo arquivo.

**Não reescreva.** Extraia em três passos, um arquivo por vez:

```
projeto/
├── public/
│   └── index.php          ← adaptador de entrada (só recebe request e delega)
├── src/
│   ├── Dominio/           ← NÚCLEO: entidades, VOs, exceções de negócio
│   ├── Aplicacao/         ← NÚCLEO: casos de uso + interfaces (portas)
│   └── Infra/             ← adaptadores: PDO, SMTP, sessão, arquivo
├── templates/             ← HTML separado da lógica
└── tests/
```

Ordem de extração, do mais fácil ao mais difícil:
1. **HTML sai primeiro** — troque `echo "<div>..."` por `include` de template. Baixo risco, ganho imediato de legibilidade.
2. **SQL vai para um repositório** — junte as queries de uma mesma tabela numa classe com métodos nomeados pelo negócio.
3. **A regra que sobrou no meio vira caso de uso** — o que restou entre receber o POST e gravar.

Sem Composer? `spl_autoload_register` resolve, ou um `require` explícito. Autoload não é pré-requisito para arquitetura.

---

## Laravel

Laravel é opinativo. O erro comum é criar `app/Domain` e continuar usando Eloquent Model como entidade — aí o núcleo depende do banco.

```
app/
├── Dominio/               ← NÚCLEO: POPOs puros, zero Illuminate
│   ├── Protocolo.php
│   └── Cpf.php
├── Aplicacao/             ← NÚCLEO: casos de uso + portas
│   ├── ArquivarProtocolo.php
│   └── RepositorioDeProtocolos.php   (interface)
├── Http/Controllers/      ← adaptador de entrada (fino)
├── Models/                ← Eloquent = detalhe de persistência, NÃO é o domínio
└── Infra/
    └── EloquentRepositorioDeProtocolos.php  ← traduz Model ↔ Entidade
```

Ligação no `AppServiceProvider`:
```php
$this->app->bind(RepositorioDeProtocolos::class, EloquentRepositorioDeProtocolos::class);
```

**O ponto que dói e vale:** o repositório converte `ProtocoloModel` (Eloquent) em `Protocolo` (domínio) e vice-versa. Parece trabalho duplicado — é o preço de o domínio não depender do banco. Em CRUD sem regra, **não pague esse preço**: use Eloquent direto no controller e siga a vida.

---

## Node / Express (e TypeScript)

```
src/
├── dominio/         ← entidades, VOs — sem import de express, sem import de driver
├── aplicacao/       ← casos de uso + interfaces de porta
├── infra/
│   ├── http/        ← rotas e controllers Express
│   ├── db/          ← implementação com pg/mysql2/Prisma
│   └── config/
└── main.ts          ← composition root: monta tudo e injeta
```

Em TypeScript, `interface` some em runtime — a injeção é manual no `main.ts` ou via container. Manual é suficiente e mais legível em projeto pequeno.

---

## Python / FastAPI

```
app/
├── dominio/         ← dataclasses frozen (VOs), entidades
├── aplicacao/       ← casos de uso + Protocol (typing) como porta
├── infra/
│   ├── api/         ← routers FastAPI
│   └── repo/        ← SQLAlchemy
└── main.py
```

`typing.Protocol` é a porta idiomática — duck typing verificado estaticamente, sem herança:
```python
class RepositorioDeProtocolos(Protocol):
    def buscar_por_numero(self, numero: NumeroProtocolo) -> Protocolo | None: ...
```

Pydantic model é **adaptador**, não entidade de domínio: ele existe para serializar HTTP.

---

## Oracle APEX / PL-SQL

APEX empurra regra para dentro de processos de página — é ali que o acoplamento nasce. O hexágono aqui é:

```
Página APEX (região, processo, validação)   ← adaptador de entrada
        │  chama
Package de API de negócio (PKG_PROTOCOLO)   ← casos de uso
        │  usa
Package de domínio + tipos                  ← regras e invariantes
        │  usa
Package de acesso a dados (PKG_PROTOCOLO_DAO) ← adaptador de saída
```

Regras práticas:
- **Processo de página não contém regra.** Ele chama uma procedure do package de negócio. Se o processo tem mais de ~10 linhas de lógica, ela pertence a um package.
- **A API de negócio não conhece `:P1_ITEM`.** Itens de página são detalhe de UI — passe como parâmetro nomeado.
- Isso torna a regra testável via `utPLSQL` e reutilizável por job, por outra página e por API REST.
- Versione os `.pks`/`.pkb` em Git como código-fonte de verdade; o export `f*.sql` da aplicação é artefato, não fonte.

---

## React / Next.js (SPA ou App Router)

Front dinâmico com estado — aqui o erro comum não é SQL vazando pro controller, é regra de negócio (validação, cálculo, decisão) vazando pra dentro de componente ou de `useEffect`, acoplada ao ciclo de vida do React.

```
src/
├── features/<dominio>/
│   └── regras.ts      ← NÚCLEO: funções puras de validação/cálculo, zero import de React
├── hooks/
│   └── useXxx.ts       ← orquestra: chama services/, aplica regras.ts, expõe estado pronto
├── services/
│   └── api.ts           ← adaptador de saída: único lugar que sabe fetch/axios/URL/headers
├── components/           ← adaptador de entrada: só JSX + evento, delega pro hook
└── store/                ← Zustand/Redux: estado global é infraestrutura, não domínio
```

**O teste de fumaça vale igual aqui:** se uma regra de validação ou cálculo só roda dentro de um componente montado — precisa de `render()`, de DOM, de mock de hook para ser testada — ela está grudada no adaptador. Extraia para uma função pura em `regras.ts` e teste sem Testing Library.

O hook (`useXxx`) é o composition root local: busca dado do `service`, aplica `regras.ts`, devolve estado já pronto. O componente não decide nada — só mostra e dispara evento. Se `ui`/componente faz `fetch` direto, é o mesmo erro do `ui.js` chamando fetch direto na seção de HTML estático acima: trocar endpoint vira caça ao tesouro no projeto inteiro.

**Erro específico de SPA, fora do hexágono clássico mas que quebra a mesma garantia de "trocar detalhe sem quebrar o resto": posição do componente na árvore importa.** Envolver um componente com estado interno caro (ex: um mapa, um player, qualquer coisa com `ref`/estado que não deveria reconstruir) num `{condicao && <div>...}` que aparece **antes** dele desloca seu índice entre os filhos — o React desmonta e remonta esse componente ao alternar a condição, mesmo sem nenhuma mudança de `key` ou prop. Sintoma: "o estado do componente X some toda vez que eu mudo Y", sem erro nenhum no console. Correção: mantenha a posição do componente estável na árvore — renderize o wrapper sempre (esconda com CSS, ex. classe `hidden`) em vez de condicionar sua presença antes de um irmão com estado.

---

## HTML estático + backend fino

Front puro consumindo API. O hexágono está todo no backend. No front, o equivalente é isolar as chamadas:

```
assets/js/
├── api.js        ← único arquivo que sabe fetch/URL/headers
├── dominio.js    ← regras de exibição/validação que existem sem tela
└── ui.js         ← manipulação de DOM
```

Se `ui.js` faz `fetch` direto, trocar a URL da API vira caça no projeto inteiro.

---

## Ecossistema multi-stack

Quando vários sistemas de stacks diferentes conversam, a fronteira entre eles é **contrato**, não banco.

- **Nunca** dois sistemas escrevendo na mesma tabela. Isso é acoplamento invisível — nenhum dos dois consegue evoluir o schema sem quebrar o outro.
- A integração é uma **porta** de cada lado: sistema A declara `ClienteDeProtocolos`, implementa com HTTP; sistema B expõe a API.
- Quando o outro sistema tem modelo ruim ou fora do seu controle, ponha uma **camada anticorrupção**: um adaptador que traduz o vocabulário deles para o seu, para a bagunça não vazar pra dentro. Ver `ddd-estrategico.md`.

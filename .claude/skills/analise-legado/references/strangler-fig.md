# Strangler Fig — substituir sem parar o sistema

Nome vem da figueira-mata-pau: ela cresce em volta da árvore hospedeira até sustentar-se sozinha, e a árvore antiga apodrece por dentro. O sistema novo cresce em volta do velho, rota por rota.

Alternativa ao *big bang rewrite*, que costuma acabar com dois sistemas incompletos rodando ao mesmo tempo.

---

## Mecânica

```
Antes:      cliente ──────────────► sistema antigo

Durante:    cliente ──► FACHADA ──┬─► sistema antigo   (rotas não migradas)
                                  └─► sistema novo     (rotas migradas)

Depois:     cliente ──► sistema novo
```

A fachada é o que torna a migração invisível para quem usa. Pode ser:
- regra de rewrite no Nginx/Apache (mais simples, e suficiente na maioria dos casos)
- um roteador em PHP no `index.php`
- proxy reverso

---

## Fachada mínima em PHP

```php
// public/index.php
$rota = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);

$migradas = [
    '/protocolos' => true,
    '/protocolos/novo' => true,
];

if (isset($migradas[$rota])) {
    require __DIR__ . '/../novo/bootstrap.php';   // hexagonal
} else {
    require __DIR__ . '/../legado/index.php';     // Frankenstein original
}
```

Lista explícita, não regex. Você deve saber, olhando, exatamente o que já migrou.

---

## Em Nginx

```nginx
location /protocolos {
    proxy_pass http://127.0.0.1:8081;   # aplicação nova
}
location / {
    proxy_pass http://127.0.0.1:8080;   # legado
}
```

---

## Ordem de migração

Escolha a primeira rota por estes critérios, nesta ordem:

1. **Poucas dependências** — idealmente lê e escreve uma tabela só
2. **Regra clara** — você já extraiu as regras dela (Fase 2 da análise)
3. **Baixo tráfego** — se der errado, dói pouco
4. **Você conhece bem** — a primeira migração é onde você aprende o padrão

**Não comece pelo módulo mais importante.** A primeira rota é treino: você vai errar a estrutura e refazer. Erre no que custa barato.

---

## O problema do banco compartilhado

Durante a migração, os dois sistemas leem e escrevem as mesmas tabelas. Isso é aceitável **temporariamente**, com duas condições:

1. O novo respeita as constraints e o formato que o antigo espera
2. Você não altera o schema até o antigo sair

Quando precisar mudar o schema antes de terminar a migração, as opções são: view de compatibilidade para o legado, ou colunas novas em paralelo (escreve nas duas, lê da nova). Ambas custam — por isso terminar a migração de um módulo antes de começar o próximo vale mais que paralelizar.

---

## Como saber que acabou

Instrumente o legado. Um log em cada ponto de entrada antigo:

```php
error_log("LEGADO_USADO: {$rota} " . date('c'));
```

Quando um arquivo não aparecer no log por semanas, ele está morto. **Aí apague — e apague de verdade, não comente.** O Git guarda; código comentado só polui a leitura.

---

## Quando NÃO usar

- Sistema pequeno o suficiente para reescrever num fim de semana com as regras já extraídas
- Sistema sem usuário ativo — se ninguém usa, migração gradual não protege ninguém
- Você não conseguiu extrair as regras do legado. Aí o problema é entendimento, não estratégia de migração — volte para a Fase 2.

---
name: api-design
description: Desenhar contratos de API e a borda HTTP de um sistema — rotas, formato de resposta, erros, versionamento, paginação, autenticação. Use quando o pedido envolver criar ou revisar endpoints, definir o JSON de resposta, decidir status codes, integrar dois sistemas por HTTP, ou expor um caso de uso existente pela web. Trata a API como adaptador de entrada da arquitetura hexagonal, não como o centro do sistema.
---

# Desenho de API

## Premissa

A API é **adaptador de entrada**, não o sistema. Ela traduz HTTP para chamada de caso de uso e traduz o retorno de volta. Se há regra de negócio dentro do controller, ela está no lugar errado — ver `arquitetura-hexagonal`.

Consequência prática: **desenhe o caso de uso primeiro, a rota depois.** A pergunta não é "que endpoint eu crio", é "que decisão o sistema toma" — o endpoint é só como ela é acionada.

## Recursos e rotas

Substantivo no plural, sem verbo na URL. O verbo é o método HTTP.

```
GET    /protocolos              lista
POST   /protocolos              cria
GET    /protocolos/{numero}     detalha
PATCH  /protocolos/{numero}     altera parcialmente
DELETE /protocolos/{numero}     remove
```

Errado: `/criarProtocolo`, `/getProtocolo`, `/protocolo/delete/5`.

**Ação que não é CRUD** — e sempre existe uma. Duas saídas honestas:

```
POST /protocolos/{numero}/arquivamento     ← trata a ação como sub-recurso
POST /protocolos/{numero}/arquivar         ← verbo explícito, pragmático
```

A primeira é mais REST-purista; a segunda é mais legível. **Escolha uma e seja consistente** — consistência vale mais que pureza. O que não vale é misturar as duas no mesmo sistema.

## Status codes que importam

Sete cobrem quase tudo:

| Código | Quando |
|---|---|
| 200 | Deu certo, tem corpo |
| 201 | Criou; devolva `Location` com a URL do novo recurso |
| 204 | Deu certo, sem corpo (típico de DELETE) |
| 400 | JSON malformado, parâmetro ausente |
| 401 | Não autenticado (não sei quem é você) |
| 403 | Autenticado, mas sem permissão (sei quem é, não pode) |
| 404 | Não existe |
| 409 | Conflito de estado — "protocolo já arquivado" |
| 422 | Sintaxe ok, regra de negócio recusou |

A confusão mais comum é 401 vs 403. A segunda mais comum é usar 400 para tudo — 422 comunica muito melhor "entendi seu pedido e o negócio recusou".

**Nunca** devolva 200 com `{"erro": "..."}` no corpo. Isso quebra todo cliente HTTP e todo monitoramento.

## Formato de erro

Escolha um formato e use em **todos** os endpoints:

```json
{
  "erro": {
    "codigo": "PROTOCOLO_JA_ARQUIVADO",
    "mensagem": "Protocolo 2024/0031 já foi arquivado em 12/03/2024.",
    "detalhes": [
      { "campo": "numero", "problema": "estado incompatível com a operação" }
    ]
  }
}
```

- `codigo` é **estável** e para máquina. O cliente compara com ele. Nunca mude o valor sem versionar.
- `mensagem` é para humano e pode mudar livremente.
- Mensagem que ajuda diz **qual valor** e **por quê**. "Erro ao processar" não ajuda ninguém às 2 da manhã.

**Nunca vaze stack trace, SQL ou caminho de arquivo** na resposta. Isso vai para o log do servidor, não para o cliente.

## Mapeamento exceção → HTTP

O caso de uso lança exceção de domínio; o adaptador traduz. Um lugar só:

```php
// infra/http/TradutorDeErros.php
match (true) {
    $e instanceof ProtocoloNaoEncontrado => [404, 'PROTOCOLO_NAO_ENCONTRADO'],
    $e instanceof ProtocoloJaArquivado   => [409, 'PROTOCOLO_JA_ARQUIVADO'],
    $e instanceof SemPermissao           => [403, 'SEM_PERMISSAO'],
    $e instanceof DadosInvalidos         => [422, 'DADOS_INVALIDOS'],
    default                              => [500, 'ERRO_INTERNO'],
};
```

O domínio **não conhece HTTP**. Ele lança `ProtocoloJaArquivado`; quem sabe que isso é 409 é a borda. É isso que permite o mesmo caso de uso servir CLI, cron e fila sem mudança.

## Paginação

Sempre, em qualquer lista. Coleção sem limite é incidente esperando data.

```
GET /protocolos?pagina=2&porPagina=25
```
```json
{
  "dados": [ ... ],
  "paginacao": { "pagina": 2, "porPagina": 25, "total": 143, "paginas": 6 }
}
```

Fixe um teto (`porPagina` máximo 100) e ignore valores acima. Cliente pedindo 100000 derruba o servidor.

Para listas grandes ou em tempo real, cursor supera offset — offset fica lento e pula registros quando há inserção durante a paginação.

## Versionamento

Comece com versão desde o primeiro endpoint: `/api/v1/protocolos`. Custa nada agora e evita a reescrita depois.

Versão nova só quando a mudança **quebra** cliente existente: remover campo, renomear campo, mudar tipo, mudar significado. **Adicionar** campo não quebra — não versione por isso.

## Integração entre sistemas

No seu ecossistema multi-stack, a API é a fronteira entre contextos. Duas regras:

1. **Do lado que consome**, a chamada HTTP fica atrás de uma porta. O caso de uso conhece `ConsultaDeServidores`, não `Guzzle`. Se a API do outro sistema for feia, o adaptador traduz e a feiura não entra — ver camada anticorrupção em `../arquitetura-hexagonal/references/ddd-estrategico.md`.
2. **Nunca integre por banco.** Dois sistemas escrevendo na mesma tabela é acoplamento invisível: nenhum consegue evoluir o schema sem quebrar o outro, e não há contrato que documente isso.

## Checklist antes de expor

- [ ] Autenticação em todas as rotas que não são públicas de propósito
- [ ] Autorização por recurso — token válido não é o mesmo que "pode ver este protocolo"
- [ ] Validação de entrada na borda, antes de chegar ao caso de uso
- [ ] Erro padronizado e sem vazamento de detalhe interno
- [ ] Paginação em toda lista
- [ ] Rate limit se for exposta fora da rede interna
- [ ] CORS restrito a origens conhecidas — `*` só em API realmente pública
- [ ] Credencial em variável de ambiente, nunca no código
- [ ] Log de erro com contexto no servidor (sem senha, sem token, sem CPF completo)

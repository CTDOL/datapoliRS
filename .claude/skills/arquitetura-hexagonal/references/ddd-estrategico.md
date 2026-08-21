# DDD estratégico — carregue só quando o problema pedir

**Não carregue este arquivo por padrão.** Ele só se paga quando existe pelo menos um destes:

- A mesma palavra significa coisas diferentes em partes diferentes do sistema
- Integração com sistema de terceiro cujo modelo você não controla
- Mais de um time mexendo no mesmo código
- Um sistema virou grande demais para uma pessoa manter o modelo inteiro na cabeça

Se nenhum se aplica, aplicar isto é cerimônia — custa arquivos e reuniões sem devolver nada.

---

## Linguagem ubíqua

Código e negócio usam **as mesmas palavras**. Se o pessoal do setor fala "tramitar", o método chama `tramitar()`, não `updateStatus()`.

Barato e vale desde o dia um, mesmo sozinho. Quando você voltar ao código em seis meses, `tramitar` continua significando algo; `updateStatus` não.

Sinal de problema: você precisa de um glossário mental para traduzir do que o usuário fala para o que o código chama.

---

## Bounded Context

Uma fronteira dentro da qual um termo tem **um** significado.

Exemplo concreto: "Servidor".
- No contexto **RH**: matrícula, lotação, data de admissão, férias
- No contexto **TI**: login, perfil de acesso, último acesso
- No contexto **Patrimônio**: responsável por bens, setor de guarda

Tentar fazer uma classe `Servidor` que sirva os três produz uma classe com 40 atributos, em que cada consumidor usa 8 e ignora o resto — e ninguém pode mudar nada sem medo.

A solução não é herança. É **três modelos separados**, cada um com o `Servidor` que faz sentido ali, ligados pela identidade (a matrícula).

**Como reconhecer que há dois contextos:** quando uma mudança pedida por um grupo de usuários quebra o que outro grupo esperava, e ambos estavam certos.

---

## Context Map — como os contextos se relacionam

Só os padrões que aparecem de fato em sistema pequeno e médio:

| Relação | Quando ocorre | O que fazer |
|---|---|---|
| **Parceria** | Dois contextos seus, evoluem juntos | Contrato combinado, mudança coordenada |
| **Cliente–Fornecedor** | O de cima define, o de baixo consome | O consumidor negocia o contrato antes |
| **Conformista** | Você consome sistema de terceiro e não tem poder de negociar | Aceita o modelo deles — mas veja anticorrupção |
| **Camada anticorrupção** | Modelo do outro é ruim ou instável | Adaptador que traduz para o seu vocabulário |
| **Kernel compartilhado** | Código comum a dois contextos | Use com parcimônia: acopla os dois para sempre |

---

## Camada anticorrupção (ACL) — o padrão que mais salva

O caso típico: você integra com um sistema legado ou externo cujo JSON tem campo `flg_st_reg = "A"` e datas como string em formato próprio.

Sem ACL, esse vocabulário se espalha pelo seu domínio e você fica refém dele para sempre.

```php
// infra/integracao/AclSistemaLegado.php  — a feiura mora aqui, e só aqui
final class AclSistemaLegado implements ConsultaDeServidores {

    public function buscar(Matricula $m): ?Servidor {
        $bruto = $this->http->get("/consulta?mat={$m}");   // vocabulário deles

        if (($bruto['flg_st_reg'] ?? '') !== 'A') {
            return null;                                    // traduz para o seu
        }
        return new Servidor(
            new Matricula($bruto['nr_mat']),
            new NomeCompleto($bruto['ds_nom_srv']),
            DateTimeImmutable::createFromFormat('dmY', $bruto['dt_adm'])
        );
    }
}
```

O núcleo conhece apenas `ConsultaDeServidores` e `Servidor`. Se o sistema deles mudar, muda **um** arquivo.

**No seu contexto multi-stack, esse é o padrão central:** cada sistema é um contexto, e a ACL é o que impede a bagunça de um contaminar o outro.

---

## Strangler Fig aplicado a contexto

Quando um sistema monolítico esconde dois contextos, não separe de uma vez:

1. Identifique a fronteira observando **quais tabelas mudam juntas** e quais grupos de usuários pedem quais mudanças.
2. Ponha uma fachada na frente do pedaço a extrair.
3. Migre um caso de uso por vez para trás da fachada.
4. Quando ninguém mais chama o código antigo direto, apague.

Detalhe operacional em `../../analise-legado/references/strangler-fig.md`.

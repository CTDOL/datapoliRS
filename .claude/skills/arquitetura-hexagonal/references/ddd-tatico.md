# DDD tático — o vocabulário do núcleo

Carregue quando for modelar o domínio de fato. Ordem de retorno sobre esforço: **value object > entidade > agregado > evento de domínio**.

---

## 1. Value Object — o de maior retorno

Um valor definido pelo que ele **é**, não por identidade. Dois CPFs com o mesmo número são o mesmo CPF. Imutável e **impossível de existir em estado inválido**.

Sem VO — validação espalhada, e sempre falta um lugar:
```php
function cadastrarServidor(string $cpf, string $matricula) {
    if (strlen($cpf) != 11) throw new Exception("CPF inválido");
    // ...e nos outros 6 lugares que recebem CPF? alguém esqueceu.
}
```

Com VO — validação existe em um lugar só, e o tipo carrega a garantia:
```php
final class Cpf {
    private string $valor;

    public function __construct(string $bruto) {
        $limpo = preg_replace('/\D/', '', $bruto);
        if (!self::digitosConferem($limpo)) {
            throw new CpfInvalido($bruto);
        }
        $this->valor = $limpo;
    }

    public function formatado(): string { /* 000.000.000-00 */ }
    public function equals(Cpf $outro): bool { return $this->valor === $outro->valor; }
}
```

Agora `function cadastrar(Cpf $cpf)` **não consegue** receber um CPF inválido. A validação virou impossibilidade estrutural em vez de checagem repetida.

**Onde isso mais rende no seu contexto:** `Matricula`, `NumeroDeProtocolo`, `Cnpj`, `Periodo` (com garantia de início ≤ fim), `Dinheiro` (valor + moeda, sem float).

**Sinal de que faltou VO:** você tem funções `validarX()` chamadas em vários lugares, e vez ou outra alguém esquece de chamar.

---

## 2. Entidade

Tem identidade que persiste mesmo quando os atributos mudam. Um servidor que troca de nome e de setor continua sendo o mesmo servidor — porque a matrícula é a mesma.

O que separa entidade de "struct com getters": **ela protege as próprias regras**.

Anêmica (regra vazou para fora):
```php
class Protocolo {
    public string $status;
    public ?DateTime $arquivadoEm;
}
// e em algum service, longe daqui:
if ($p->status === 'ARQUIVADO') { /* alguém vai esquecer essa checagem */ }
$p->status = 'ARQUIVADO';
```

Rica (a regra mora com o dado):
```php
class Protocolo {
    private StatusProtocolo $status;

    public function arquivar(Servidor $responsavel): void {
        if ($this->status->ehArquivado()) {
            throw new ProtocoloJaArquivado($this->numero);
        }
        if (!$responsavel->podeArquivar()) {
            throw new SemPermissaoParaArquivar();
        }
        $this->status = StatusProtocolo::arquivado();
        $this->registrarEvento(new ProtocoloArquivado($this->numero, $responsavel));
    }
}
```

Agora é **impossível** arquivar duas vezes, de qualquer lugar do sistema. A regra não depende de ninguém lembrar de checar.

> Modelo anêmico não é sempre erro. Em CRUD sem regra, entidade anêmica é honesta — não invente comportamento onde não há decisão.

---

## 3. Agregado

Um grupo de entidades tratado como unidade de consistência, com **uma raiz** que é o único ponto de entrada.

Exemplo: `Processo` (raiz) contém `Movimentacao[]`. Ninguém pega uma movimentação solta e altera — pede ao processo.

```php
class Processo {
    private array $movimentacoes = [];

    public function movimentar(Setor $destino, Servidor $por): void {
        if ($this->estaArquivado()) throw new ProcessoArquivado();
        if ($this->setorAtual()->equals($destino)) throw new MovimentacaoRedundante();
        $this->movimentacoes[] = new Movimentacao($destino, $por, new DateTimeImmutable());
    }
}
```

**Três regras práticas:**
1. Repositório existe **por agregado**, nunca por entidade interna. Existe `RepositorioDeProcessos`, não `RepositorioDeMovimentacoes`.
2. Uma transação salva **um** agregado. Se precisa salvar dois atomicamente, provavelmente é um agregado só — ou a consistência entre eles pode ser eventual.
3. Mantenha pequeno. Agregado grande vira gargalo de lock e carga.

**Referência entre agregados é por identidade, não por objeto:** `Processo` guarda `MatriculaDoResponsavel`, não o objeto `Servidor` inteiro.

---

## 4. Evento de domínio

"Algo relevante para o negócio aconteceu", no passado. `ProtocoloArquivado`, `ServidorTransferido`.

Serve para desacoplar efeitos colaterais. Sem evento, `arquivar()` acaba chamando e-mail, log e integração — e o domínio passa a conhecer SMTP.

```php
// dentro do agregado: só registra
$this->registrarEvento(new ProtocoloArquivado($this->numero));

// o caso de uso publica; adaptadores reagem
foreach ($protocolo->eventos() as $evento) {
    $this->publicador->publicar($evento);
}
```

**Adie isso.** Em sistema de um dev, chamar o efeito direto no caso de uso é aceitável. Evento se paga quando os assinantes começam a se multiplicar ou o efeito precisa ser assíncrono.

---

## 5. Repositório

A porta de persistência, em vocabulário de domínio. Ver `../SKILL.md` seção "Portas".

Duas armadilhas comuns:
- **Repositório genérico** (`Repository<T>` com `findAll`, `findBy`) — devolve o acoplamento ao ORM por outro caminho. Prefira métodos que digam o que o negócio pergunta: `listarPendentesDe(Setor)`.
- **Vazamento de query builder** — se o método devolve um builder para o caso de uso continuar montando a query, a tecnologia atravessou a porta.

---

## Sequência recomendada ao modelar

1. Escreva **uma frase** do que o sistema decide. Se não conseguir, ainda não há domínio — talvez seja CRUD.
2. Sublinhe os substantivos → candidatos a entidade e VO.
3. Sublinhe os verbos → candidatos a método de entidade ou caso de uso.
4. Pergunte de cada substantivo: *"se dois tiverem os mesmos valores, são a mesma coisa?"* Sim → value object. Não → entidade.
5. Agrupe o que precisa mudar junto → agregado; escolha a raiz.
6. Declare os repositórios (um por raiz).

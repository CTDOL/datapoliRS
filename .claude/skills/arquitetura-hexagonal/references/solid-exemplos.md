# SOLID — violação e correção, lado a lado

Referência de consulta. Cada princípio tem o cheiro que denuncia, o exemplo errado e a correção.

---

## S — Responsabilidade única

**Cheiro:** a classe tem "e" na descrição. "Processa o pedido *e* envia e-mail *e* grava log."
**Teste real:** quantos motivos diferentes fariam esse arquivo mudar?

Errado — três razões para mudar (regra, e-mail, log):
```php
class ProcessadorDeProtocolo {
    public function processar(array $dados) {
        // regra
        if ($dados['tipo'] === 'urgente') { $prazo = 24; } else { $prazo = 120; }
        // persistência
        $this->pdo->prepare("INSERT INTO protocolos ...")->execute($dados);
        // notificação
        mail($dados['email'], 'Protocolo criado', "Prazo: $prazo h");
        // auditoria
        file_put_contents('/var/log/app.log', date('c') . " criado\n", FILE_APPEND);
    }
}
```

Certo — cada peça muda por seu próprio motivo:
```php
class CriarProtocolo {                       // muda se a REGRA mudar
    public function __construct(
        private RepositorioDeProtocolos $repo,   // muda se o BANCO mudar
        private Notificador $notificador,        // muda se o CANAL mudar
    ) {}

    public function executar(DadosDoProtocolo $dados): Protocolo {
        $protocolo = Protocolo::criar($dados);   // regra mora na entidade
        $this->repo->salvar($protocolo);
        $this->notificador->notificar($protocolo);
        return $protocolo;
    }
}
```

Nota: "responsabilidade única" **não** significa "uma função por classe". Significa um eixo de mudança.

---

## O — Aberto para extensão, fechado para modificação

**Cheiro:** um `switch`/`if-elseif` sobre tipo, que cresce toda vez que aparece um caso novo.

Errado:
```php
function calcularPrazo(string $tipo): int {
    if ($tipo === 'urgente')   return 24;
    if ($tipo === 'ordinario') return 120;
    if ($tipo === 'sigiloso')  return 48;   // e a cada tipo novo, editar aqui
}
```

Certo — tipo novo é classe nova, o código existente não é tocado:
```php
interface TipoDeProtocolo {
    public function prazoEmHoras(): int;
}
final class Urgente   implements TipoDeProtocolo { public function prazoEmHoras(): int { return 24; } }
final class Sigiloso  implements TipoDeProtocolo { public function prazoEmHoras(): int { return 48; } }
```

**Ressalva honesta:** não abstraia no primeiro `if`. A regra prática é *três ocorrências* — dois casos podem muito bem continuar um `if`. Abstração prematura custa mais que o `switch`.

---

## L — Substituição de Liskov

**Cheiro:** `instanceof` dentro de quem consome a interface; ou uma implementação que lança "não suportado".

Errado:
```php
class RepositorioSomenteLeitura implements RepositorioDeProtocolos {
    public function salvar(Protocolo $p): void {
        throw new BadMethodCallException("não suporta escrita");   // quebra o contrato
    }
}
```
Quem recebe a interface não pode confiar nela — precisa saber qual implementação chegou.

Certo — separe os contratos:
```php
interface LeitorDeProtocolos { public function buscarPorNumero(NumeroProtocolo $n): ?Protocolo; }
interface EscritorDeProtocolos { public function salvar(Protocolo $p): void; }
```

---

## I — Segregação de interfaces

**Cheiro:** implementação cheia de método vazio ou `return null` só para satisfazer a interface.

Errado — quem só exporta CSV é obrigado a implementar tudo:
```php
interface Relatorio {
    public function gerarPdf(): string;
    public function gerarCsv(): string;
    public function gerarXlsx(): string;
    public function enviarPorEmail(): void;
}
```

Certo — capacidades separadas, cada exportador implementa o que faz:
```php
interface ExportaCsv { public function gerarCsv(): string; }
interface ExportaPdf { public function gerarPdf(): string; }
```

---

## D — Inversão de dependência

O princípio que sustenta o hexágono inteiro. **A regra não instancia a tecnologia; ela declara o que precisa.**

**Cheiro:** `new PDO(...)`, `new Mailer(...)`, `DB::table(...)` dentro de um caso de uso ou entidade.

Errado — o caso de uso está soldado ao MySQL:
```php
class ArquivarProtocolo {
    public function executar(string $numero) {
        $pdo = new PDO('mysql:host=localhost;dbname=app', 'root', 'senha');
        $pdo->prepare("UPDATE protocolos SET status='ARQUIVADO' WHERE numero=?")
            ->execute([$numero]);
    }
}
```
Não dá para testar sem MySQL. Não dá para trocar o banco. E a regra "não arquivar duas vezes" não existe em lugar nenhum.

Certo:
```php
class ArquivarProtocolo {
    public function __construct(private RepositorioDeProtocolos $repo) {}   // porta

    public function executar(NumeroProtocolo $numero, Servidor $por): void {
        $protocolo = $this->repo->buscarPorNumero($numero)
            ?? throw new ProtocoloNaoEncontrado($numero);
        $protocolo->arquivar($por);        // regra na entidade
        $this->repo->salvar($protocolo);
    }
}
```
Testável com um repositório em memória, em milissegundos, sem infraestrutura.

---

## Onde ligar tudo: composition root

A inversão precisa de um lugar onde as dependências concretas são escolhidas — **um só**, na borda da aplicação.

```php
// public/index.php  — o único lugar que conhece as classes concretas
$pdo  = new PDO($dsn, $user, $pass);
$repo = new PdoRepositorioDeProtocolos($pdo);
$caso = new ArquivarProtocolo($repo);
$caso->executar(new NumeroProtocolo($_POST['numero']), $servidorLogado);
```

Container de injeção é conveniência, não requisito. Em projeto pequeno, montar à mão no `index.php` é mais claro do que configurar container — e deixa a dependência visível.

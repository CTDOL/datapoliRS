# Teste de caracterização — como testar o intestável

O objetivo não é provar que o código está certo. É **detectar mudança**. Ele congela o comportamento atual, bugs inclusive, para que a refatoração tenha um sensor.

---

## Passo a passo

1. Escreva um teste que chama o código com uma entrada plausível.
2. Afirme um valor **qualquer** (ex.: `assertSame('XXX', $r)`).
3. Rode. O teste falha e a mensagem te diz o valor real.
4. Troque a afirmação pelo valor real.
5. Repita para cada caminho relevante.

Você não precisa entender a regra para escrever o teste. Ele documenta o que É, não o que deveria ser. O entendimento vem depois, lendo os testes juntos.

---

## Quando o código é acoplado demais

### Caso 1 — a função vai ao banco

Não mocke o banco. Use **banco real descartável**, que é mais fiel e mais barato de montar:

```php
// SQLite em memória, recriado a cada teste
$pdo = new PDO('sqlite::memory:');
$pdo->exec(file_get_contents('tests/fixtures/schema.sql'));
$pdo->exec("INSERT INTO protocolos VALUES (1,'2024/001','urgente','ABERTO')");
```

Se o SQL usa dialeto específico do MySQL, suba um MySQL em Docker só para o teste. No seu laboratório isso é trivial e vale mais que qualquer mock.

### Caso 2 — estado global (`$_POST`, `$_SESSION`, singleton)

Ajuste o global antes de chamar, restaure depois:

```php
protected function setUp(): void {
    $this->postOriginal = $_POST;
    $_POST = ['tipo' => 'urgente', 'setor' => 'DTIC'];
}
protected function tearDown(): void { $_POST = $this->postOriginal; }
```

Feio de propósito. O teste feio existe para você poder tornar o código bonito — e some depois que a dependência de global for extraída.

### Caso 3 — a função imprime em vez de retornar

Capture a saída:

```php
ob_start();
renderizarRelatorio($dados);
$html = ob_get_clean();
$this->assertStringContainsString('<td>24</td>', $html);
```

Afirme sobre **um fragmento estável**, não sobre o HTML inteiro — senão qualquer mudança de espaçamento quebra o teste e você perde a confiança nele.

### Caso 4 — nada é testável isoladamente

**Teste de aproximação (golden master).** Trate o sistema inteiro como caixa-preta:

```bash
# ANTES de mexer — gerar o retrato
for entrada in tests/entradas/*.json; do
  php cli.php < "$entrada" > "tests/golden/$(basename "$entrada").out"
done

# DEPOIS de cada refatoração — comparar
for entrada in tests/entradas/*.json; do
  php cli.php < "$entrada" > /tmp/atual.out
  diff -u "tests/golden/$(basename "$entrada").out" /tmp/atual.out \
    || echo "MUDOU: $entrada"
done
```

Gere muitas entradas — inclusive absurdas: campo vazio, texto onde espera número, data inválida, acento, string gigante. **É nos casos absurdos que o comportamento não documentado mora.**

Cuidado com saída que varia sozinha (data atual, ID auto-increment, ordem aleatória). Normalize antes de comparar, ou o teste vira falso alarme e você para de confiar nele.

---

## Quantos testes bastam?

Não busque cobertura alta. Busque cobrir **o que você vai tocar**.

Antes de refatorar o cálculo de prazo: teste cada tipo de prazo, mais os limites, mais o caso inválido. Cinco testes. O resto do sistema pode continuar sem teste — você não vai mexer nele agora.

---

## Depois da refatoração

Os testes de caracterização mudam de papel:

- Os que congelaram **comportamento correto** → viram teste de regressão. Ficam.
- Os que congelaram **bug** → corrija o bug em commit separado, ajuste o teste na mesma mudança, e escreva no commit por que o comportamento mudou.

**Nunca** corrija bug e refatore estrutura no mesmo commit. Quando algo quebrar depois, você não vai saber qual dos dois causou.

---
name: repo-bootstrap
description: Colocar um projeto sob controle de versão e configurar o repositório no GitHub — .gitignore adequado à stack, proteção de credenciais, workflow de CI, templates de PR e issue, convenção de commit. Use quando o projeto não estiver em Git, quando faltar CI ou automação, quando for publicar um repositório, ou quando o usuário pedir para "configurar o GitHub" ou padronizar o repositório. Inclui o procedimento para credencial que já foi commitada.
---

# Bootstrap de repositório

## Ordem obrigatória

**Credencial antes de remoto.** Uma vez que você faz `git push` com senha no código, ela está publicada — mesmo em repositório privado, mesmo se você apagar depois. Reescrever histórico não desfaz: quem clonou, tem.

```
1. Varrer credenciais    →  2. .gitignore     →  3. git init + commit
                                                       ↓
6. CI e templates    ←     5. push       ←     4. criar remoto
```

## Passo 1 — Varrer credenciais

```bash
grep -rnE "(password|senha|secret|api_key|token|DB_PASS)[[:space:]]*=[[:space:]]*[\"'][^\"']{3,}" \
  --include='*.php' --include='*.js' --include='*.py' --include='*.ts' \
  --exclude-dir=vendor --exclude-dir=node_modules .
```

Verifique também: `config.php`, `.env`, `wp-config.php`, dumps `.sql` (contêm dados reais), backups `.bak`, e `.zip` esquecidos na raiz.

Para cada achado: mova para variável de ambiente, deixe `.env.example` com a chave e valor vazio, e **troque a credencial** se ela já esteve num repositório em algum momento.

## Passo 2 — .gitignore

Comece pelo template da stack em `assets/` e adicione o que for específico. Regra: **nunca versione** o que é gerado (`vendor/`, `node_modules/`, `dist/`), o que é local (`.env`, `*.log`, `.DS_Store`) e o que é dado (`*.sqlite`, dumps).

`.env.example` **vai** para o repositório. `.env` **nunca**.

## Passo 3 — Git local

```bash
git init
git add -A
git status          # LEIA a lista antes de commitar
git commit -m "chore: estado inicial do projeto"
```

O `git status` antes do primeiro commit é o último ponto onde dá para evitar publicar o que não devia. Não pule.

## Passo 4 e 5 — Remoto

```bash
git remote add origin git@github.com:ORG/REPO.git
git branch -M main
git push -u origin main
```

Prefira SSH a HTTPS: sem token colado em prompt, sem credencial em cache. Para conta organizacional, confirme que a chave SSH está associada à conta certa antes.

## Passo 6 — CI

Copie de `assets/workflows/` conforme a stack. O que a CI deve fazer, em ordem de valor:

1. **Rodar os testes** — a razão de existir
2. **Checar sintaxe/lint** — barato e pega erro bobo
3. **Auditar dependências** — `npm audit`, `composer audit`
4. **Varrer credencial no diff** — impede reincidência

Se ainda não há teste, comece com lint e sintaxe. CI que não roda nada útil ensina o time a ignorar o ✗ vermelho — e aí ela perde a função para sempre.

## Convenção de commit

```
feat:     funcionalidade nova
fix:      correção de bug
refactor: muda estrutura sem mudar comportamento
test:     adiciona ou corrige teste
chore:    build, config, dependência
docs:     documentação
```

O valor real aparece na refatoração: `refactor:` significa **comportamento idêntico**. Se você misturar correção de bug num commit `refactor:`, perde a única garantia que essa convenção oferece — e é justamente a que importa quando algo quebra depois.

## Se a credencial já foi commitada

Nesta ordem, sem inverter:

1. **Troque a credencial agora.** Senha, chave, token — gere nova. Este passo é o único que realmente resolve.
2. Remova do código, mova para `.env`, commite.
3. Limpar o histórico (`git filter-repo`, BFG) é **opcional e secundário**. Reduz exposição futura; não desfaz a exposição que já houve.

Invertar a ordem é o erro comum: gasta-se a tarde limpando histórico com a senha antiga ainda válida.

## Estrutura mínima do repositório

```
.gitignore
.env.example
README.md              o que é, como rodar, como testar
.github/
├── workflows/ci.yml
├── pull_request_template.md
└── ISSUE_TEMPLATE/bug.md
```

README que serve responde três perguntas: **o que esse sistema faz** (em uma frase de negócio, não técnica), **como subir localmente**, **como rodar os testes**. O resto é bônus.

## Repositório para laboratório

Se o projeto é experimento pessoal, pule templates de issue e PR — não há com quem colaborar, e formulário vazio só atrapalha. Mantenha o essencial: `.gitignore`, `.env.example`, README e CI rodando os testes. Isso já entrega o valor principal, que é **poder voltar atrás e saber o que mudou**.

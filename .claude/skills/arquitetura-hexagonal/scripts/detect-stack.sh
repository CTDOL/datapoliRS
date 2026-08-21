#!/usr/bin/env bash
# detect-stack.sh — inventário rápido de um projeto antes de propor arquitetura.
# Uso: ./detect-stack.sh [diretorio]   (padrão: diretório atual)
# Somente leitura. Não altera nada.

set -uo pipefail
DIR="${1:-.}"
cd "$DIR" 2>/dev/null || { echo "ERRO: diretório inacessível: $DIR"; exit 1; }
RAIZ="$(pwd)"

linha() { printf '%s\n' "------------------------------------------------------------"; }
tem()   { [ -e "$1" ]; }

echo "INVENTÁRIO DO PROJETO"
echo "Diretório: $RAIZ"
echo "Data: $(date '+%Y-%m-%d %H:%M')"
linha

# ---------- STACKS ----------
echo "STACKS DETECTADAS"
ACHOU=0
marca() { echo "  - $1"; ACHOU=1; }

tem package.json      && marca "Node.js  (package.json)"
tem composer.json     && marca "PHP/Composer (composer.json)"
tem pyproject.toml    && marca "Python   (pyproject.toml)"
tem requirements.txt  && marca "Python   (requirements.txt)"
tem Gemfile           && marca "Ruby     (Gemfile)"
tem go.mod            && marca "Go       (go.mod)"
tem pom.xml           && marca "Java/Maven (pom.xml)"
tem build.gradle      && marca "Java/Gradle (build.gradle)"
tem artisan           && marca "Laravel  (artisan)"
tem manage.py         && marca "Django   (manage.py)"
tem Dockerfile        && marca "Docker   (Dockerfile)"
tem docker-compose.yml && marca "Docker Compose"

# PHP procedural: .php na raiz sem composer
if [ ! -f composer.json ] && [ "$(find . -maxdepth 2 -name '*.php' 2>/dev/null | head -1)" ]; then
  marca "PHP procedural / sem gerenciador de dependência"
fi
# Front estático
if [ -f index.html ] && [ ! -f package.json ]; then
  marca "HTML estático (index.html sem build)"
fi
# Oracle / APEX
if find . -maxdepth 3 \( -name '*.pks' -o -name '*.pkb' -o -name '*.plb' \) 2>/dev/null | grep -q .; then
  marca "Oracle PL/SQL (pacotes)"
fi
if find . -maxdepth 3 -name 'f*.sql' 2>/dev/null | head -1 | grep -q .; then
  marca "Possível export de aplicação Oracle APEX (f*.sql)"
fi

[ "$ACHOU" -eq 0 ] && echo "  (nenhuma stack reconhecida automaticamente)"
linha

# ---------- FRAMEWORK PHP ----------
if [ -f composer.json ]; then
  echo "DEPENDÊNCIAS PHP PRINCIPAIS"
  grep -oE '"(laravel/framework|symfony/[a-z-]+|slim/slim|cakephp/cakephp)"[^,]*' composer.json 2>/dev/null \
    | head -8 | sed 's/^/  /' || echo "  (não identificadas)"
  linha
fi

# ---------- GIT ----------
echo "CONTROLE DE VERSÃO"
if [ -d .git ]; then
  echo "  Git: SIM"
  echo "  Branch: $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?')"
  echo "  Commits: $(git rev-list --count HEAD 2>/dev/null || echo 0)"
  SUJO=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
  echo "  Arquivos não commitados: $SUJO"
  [ "$SUJO" -gt 0 ] && echo "  >> ATENÇÃO: há alterações não commitadas. Commite ou faça snapshot antes de refatorar."
  echo "  Último commit: $(git log -1 --format='%ad (%ar)' --date=short 2>/dev/null || echo '?')"
else
  echo "  Git: NÃO"
  echo "  >> Sem histórico. Rode analise-legado/scripts/snapshot.sh antes de qualquer edição."
fi
linha

# ---------- TESTES ----------
echo "TESTES"
T=0
for p in tests test spec __tests__ Test; do
  if [ -d "$p" ]; then echo "  Diretório de teste: $p/"; T=1; fi
done
N=$(find . -path ./node_modules -prune -o -path ./vendor -prune -o \
     \( -name '*.test.*' -o -name '*.spec.*' -o -name 'test_*.py' -o -name '*Test.php' \) -print 2>/dev/null | wc -l | tr -d ' ')
echo "  Arquivos de teste encontrados: $N"
[ "$N" -eq 0 ] && [ "$T" -eq 0 ] && echo "  >> Sem testes. Refatoração exige teste de caracterização antes. Ver analise-legado."
linha

# ---------- TAMANHO ----------
echo "TAMANHO"
CODE=$(find . -path ./node_modules -prune -o -path ./vendor -prune -o -path ./.git -prune -o \
       \( -name '*.php' -o -name '*.js' -o -name '*.ts' -o -name '*.py' -o -name '*.rb' \
          -o -name '*.go' -o -name '*.java' -o -name '*.sql' \) -print 2>/dev/null)
QTD=$(echo "$CODE" | grep -c . || echo 0)
LIN=$(echo "$CODE" | tr '\n' '\0' 2>/dev/null | xargs -0 wc -l 2>/dev/null | tail -1 | awk '{print $1}')
echo "  Arquivos de código: $QTD"
echo "  Linhas totais: ${LIN:-0}"

echo "  Maiores arquivos:"
echo "$CODE" | tr '\n' '\0' 2>/dev/null | xargs -0 wc -l 2>/dev/null \
  | sort -rn | grep -v ' total$' | head -5 | sed 's/^/    /'
echo "  >> Arquivo acima de ~500 linhas costuma esconder mais de uma responsabilidade."
linha

# ---------- SINAIS DE ACOPLAMENTO ----------
echo "SINAIS DE ACOPLAMENTO (heurística — confirmar lendo o código)"
SQL=$(grep -rlE "(SELECT|INSERT|UPDATE|DELETE)[[:space:]]" --include='*.php' --include='*.js' --include='*.ts' --include='*.py' \
      --exclude-dir=vendor --exclude-dir=node_modules . 2>/dev/null | wc -l | tr -d ' ')
echo "  Arquivos com SQL embutido: $SQL"
[ "$SQL" -gt 3 ] && echo "    >> SQL espalhado indica ausência de camada de repositório."

ECHOHTML=$(grep -rlE "(echo|print)[[:space:]]+[\"'][[:space:]]*<" --include='*.php' --exclude-dir=vendor . 2>/dev/null | wc -l | tr -d ' ')
[ "$ECHOHTML" -gt 0 ] && echo "  Arquivos PHP misturando HTML e lógica: $ECHOHTML"

CRED=$(grep -rlE "(password|senha|secret|api_key)[[:space:]]*=[[:space:]]*[\"'][^\"']{3,}" \
       --include='*.php' --include='*.js' --include='*.py' --exclude-dir=vendor --exclude-dir=node_modules . 2>/dev/null | wc -l | tr -d ' ')
[ "$CRED" -gt 0 ] && echo "  >> ALERTA: $CRED arquivo(s) com possível credencial hardcoded. Verificar antes de subir ao Git."
linha

echo "PRÓXIMO PASSO"
echo "  Com esse retrato, identifique a REGRA DE NEGÓCIO antes de propor pastas."
echo "  Sem git ou sem teste -> passar por analise-legado antes de refatorar."

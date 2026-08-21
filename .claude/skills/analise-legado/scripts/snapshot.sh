#!/usr/bin/env bash
# snapshot.sh — ponto de retorno antes de refatorar.
# Uso: ./snapshot.sh [diretorio] [destino-backup]
# Cria tar.gz datado e, se não houver Git, inicializa com commit do estado atual.

set -euo pipefail
DIR="${1:-.}"
cd "$DIR" 2>/dev/null || { echo "ERRO: diretório inacessível: $DIR"; exit 1; }
RAIZ="$(pwd)"
NOME="$(basename "$RAIZ")"
DEST="${2:-$HOME/snapshots}"
STAMP="$(date '+%Y%m%d-%H%M%S')"

mkdir -p "$DEST"
ARQ="$DEST/${NOME}_${STAMP}.tar.gz"

echo "SNAPSHOT"
echo "  Origem:  $RAIZ"
echo "  Destino: $ARQ"
echo

# ---------- 1. Tarball ----------
tar --exclude='./node_modules' \
    --exclude='./vendor' \
    --exclude='./.git' \
    --exclude='*.log' \
    -czf "$ARQ" . 2>/dev/null || {
      echo "AVISO: tar terminou com erro parcial; verifique o arquivo gerado."
    }

if [ -f "$ARQ" ]; then
  TAM=$(du -h "$ARQ" | cut -f1)
  echo "  [ok] Backup criado ($TAM)"
else
  echo "  [FALHA] Backup não foi criado. NÃO prossiga com a refatoração."
  exit 1
fi

# ---------- 2. Git ----------
echo
echo "GIT"
if [ -d .git ]; then
  SUJO=$(git status --porcelain | wc -l | tr -d ' ')
  if [ "$SUJO" -gt 0 ]; then
    echo "  Repositório já existe, com $SUJO alteração(ões) não commitada(s)."
    echo "  Criando commit de ponto de partida..."
    git add -A
    git commit -q -m "snapshot: estado antes de refatorar ($STAMP)" || echo "  (nada a commitar)"
    echo "  [ok] Commit criado."
  else
    echo "  [ok] Repositório limpo. Commit atual serve como ponto de retorno:"
    git log -1 --format='       %h %s' 2>/dev/null
  fi
else
  echo "  Sem Git. Inicializando..."
  cat > .gitignore <<'GITIGNORE'
node_modules/
vendor/
*.log
.env
.env.*
!.env.example
composer.lock
package-lock.json
.DS_Store
*.sqlite
GITIGNORE
  git init -q
  git add -A
  git -c user.email="lab@local" -c user.name="snapshot" \
      commit -q -m "snapshot: estado original antes de refatorar ($STAMP)"
  echo "  [ok] Git inicializado com commit do estado original."
  echo "       .gitignore básico criado — revise antes de adicionar remoto."
fi

# ---------- 3. Aviso de credenciais ----------
echo
echo "VERIFICAÇÃO DE CREDENCIAIS"
ACHOU=$(grep -rlE "(password|senha|secret|api_key|token)[[:space:]]*=[[:space:]]*[\"'][^\"']{3,}" \
        --include='*.php' --include='*.js' --include='*.py' --include='*.ts' \
        --exclude-dir=vendor --exclude-dir=node_modules --exclude-dir=.git . 2>/dev/null || true)
if [ -n "$ACHOU" ]; then
  echo "  >> ATENÇÃO: possível credencial em:"
  echo "$ACHOU" | sed 's/^/       /'
  echo "  >> Mova para .env ANTES de adicionar um remoto no GitHub."
  echo "  >> Se já foi commitado antes, trocar a senha é obrigatório —"
  echo "     remover do histórico não basta, ela já circulou."
else
  echo "  [ok] Nenhuma credencial óbvia encontrada (heurística — confira manualmente)."
fi

echo
echo "PRONTO. Para voltar ao estado atual:"
echo "  git reset --hard HEAD          (se usar git)"
echo "  tar -xzf $ARQ -C <destino>     (do backup)"

#!/usr/bin/env bash
# audit-servidor.sh — inventário somente-leitura de um servidor/VPS.
# Uso: ./audit-servidor.sh
# Rode DENTRO do servidor a ser auditado (via SSH). Não altera nada.
# Partes que exigem sudo avisam e seguem sem travar o resto do script.

set -uo pipefail

linha() { printf '%s\n' "------------------------------------------------------------"; }
tem_cmd() { command -v "$1" >/dev/null 2>&1; }

echo "AUDITORIA DE SERVIDOR — $(hostname 2>/dev/null || echo '?')"
echo "Data: $(date '+%Y-%m-%d %H:%M %Z')"
linha

# ---------- PAINEL DE CONTROLE / VIRTUALIZAÇÃO ----------
if [ -d /usr/local/cpanel ]; then
  echo "PAINEL: cPanel/WHM detectado"
  echo "  >> Vhosts e certificados ficam POR CONTA, fora dos caminhos padrão de"
  echo "     Apache/Nginx/Let's Encrypt. 'Não encontrado' abaixo NÃO significa"
  echo "     'não existe' — confirme domínios e SSL via WHM/AutoSSL."
  echo "  >> Ao medir disco: o cPanel usa virtfs e faz bind-mount de /usr, /var"
  echo "     dentro de /home/virtfs/<conta>/. O 'du' conta em duplicidade."
  echo "     Confie no 'df', não no 'du' da raiz."
  linha
fi

# ---------- SISTEMA ----------
echo "SISTEMA"
if [ -f /etc/os-release ]; then
  . /etc/os-release
  echo "  Distro: ${PRETTY_NAME:-desconhecida}"
fi
echo "  Kernel: $(uname -r 2>/dev/null || echo '?')"
echo "  Uptime: $(uptime -p 2>/dev/null || uptime 2>/dev/null || echo '?')"
echo "  Carga: $(cat /proc/loadavg 2>/dev/null | awk '{print $1, $2, $3}' || echo '?')"
if tem_cmd free; then
  echo "  Memória: $(free -h 2>/dev/null | awk '/^Mem:/{print $3"/"$2" usados"}')"
fi
if tem_cmd df; then
  echo "  Disco (/): $(df -h / 2>/dev/null | awk 'NR==2{print $3"/"$2" usados ("$5")"}')"
fi
linha

# ---------- ATUALIZAÇÕES PENDENTES ----------
echo "ATUALIZAÇÕES DO SISTEMA"
if tem_cmd apt; then
  N=$(apt list --upgradable 2>/dev/null | grep -c upgradable || echo 0)
  echo "  Pacotes com atualização pendente (apt): $N"
  [ "$N" -gt 0 ] && echo "  >> Reinício pode ser necessário depois de atualizar kernel/libs críticas."
elif tem_cmd dnf; then
  N=$(dnf check-update 2>/dev/null | grep -cE '^[a-zA-Z0-9]' || echo 0)
  echo "  Pacotes com atualização pendente (dnf): $N"
elif tem_cmd yum; then
  echo "  Gerenciador: yum — rode 'yum check-update' manualmente para o total."
else
  echo "  Gerenciador de pacotes não identificado automaticamente."
fi
linha

# ---------- SERVIÇOS ----------
echo "SERVIÇOS ATIVOS (systemd)"
if tem_cmd systemctl; then
  systemctl list-units --type=service --state=running 2>/dev/null \
    | grep -v '^$' | grep -v '^UNIT' | grep -v 'loaded units listed' \
    | awk '{print "  - "$1}' | head -40
  TOTAL=$(systemctl list-units --type=service --state=running 2>/dev/null | grep -c '\.service')
  echo "  Total: $TOTAL serviços rodando"
else
  echo "  systemd não encontrado — verificar init alternativo (sysvinit, OpenRC) manualmente."
fi
linha

# ---------- CONTAINERS ----------
if tem_cmd docker; then
  echo "DOCKER"
  echo "  Containers rodando:"
  docker ps --format '    - {{.Names}} ({{.Image}}) — portas: {{.Ports}}' 2>/dev/null \
    || echo "    (sem permissão — rode com sudo ou usuário no grupo docker)"
  if [ -f docker-compose.yml ] || [ -f compose.yml ]; then
    echo "  >> docker-compose encontrado no diretório atual."
  fi
  linha
fi

# ---------- PORTAS ----------
echo "PORTAS ESCUTANDO"
if tem_cmd ss; then
  ss -tlnp 2>/dev/null | tail -n +2 | awk '{print "  "$1" "$4" "$NF}' \
    || ss -tln 2>/dev/null | tail -n +2 | awk '{print "  "$1" "$4}'
  echo "  >> Porta escutando em 0.0.0.0 ou :: está exposta a qualquer interface — confirme se precisa mesmo estar assim."
elif tem_cmd netstat; then
  netstat -tlnp 2>/dev/null | tail -n +3 | awk '{print "  "$1" "$4" "$NF}'
else
  echo "  Nenhuma ferramenta (ss/netstat) disponível para checar portas."
fi
linha

# ---------- FIREWALL ----------
echo "FIREWALL"
if tem_cmd ufw; then
  echo "  ufw status:"
  ufw status verbose 2>/dev/null | sed 's/^/    /' || echo "    (precisa de sudo)"
elif tem_cmd firewall-cmd; then
  echo "  firewalld ativo: $(firewall-cmd --state 2>/dev/null || echo '?')"
  firewall-cmd --list-all 2>/dev/null | sed 's/^/    /'
elif tem_cmd iptables; then
  echo "  Sem ufw/firewalld. Regras iptables cruas (INPUT):"
  REGRAS=$(iptables -L INPUT -n -v 2>/dev/null | tail -n +3 | grep -v '^\s*$' || true)
  if [ -n "$REGRAS" ]; then
    echo "$REGRAS" | head -30 | sed 's/^/    /'
    POLICY=$(iptables -L INPUT -n 2>/dev/null | head -1)
    echo "    Política padrão: $POLICY"
    echo "$POLICY" | grep -q 'policy ACCEPT' && \
      echo "  >> ALERTA: política padrão ACCEPT — sem regra de bloqueio, TODA porta que um processo abrir fica exposta."
  else
    echo "    (sem permissão para ler as regras — rode com sudo)"
  fi
else
  echo "  Nenhum firewall identificado. >> ALERTA: confirmar se há proteção na camada de rede/provedor."
fi
linha

# ---------- SERVIDOR WEB E VHOSTS ----------
echo "SERVIDOR WEB"
if tem_cmd nginx; then
  echo "  Nginx encontrado."
  echo "  Sites habilitados:"
  find /etc/nginx/sites-enabled /etc/nginx/conf.d -maxdepth 1 -type f 2>/dev/null \
    | sed 's/^/    /' || echo "    (nenhum em sites-enabled/conf.d — checar nginx.conf diretamente)"
elif [ -d /etc/apache2 ] || tem_cmd apache2ctl || tem_cmd httpd; then
  echo "  Apache encontrado."
  find /etc/apache2/sites-enabled /etc/httpd/conf.d -maxdepth 1 -type f 2>/dev/null \
    | sed 's/^/    /' || echo "    (nenhum vhost encontrado nos caminhos padrão)"
else
  echo "  Nenhum servidor web tradicional detectado (pode estar em container — ver seção DOCKER)."
fi
linha

# ---------- CERTIFICADOS SSL ----------
echo "CERTIFICADOS SSL"
if [ -d /etc/letsencrypt/live ]; then
  for dom in /etc/letsencrypt/live/*/; do
    [ -d "$dom" ] || continue
    NOME=$(basename "$dom")
    CERT="$dom/cert.pem"
    if [ -f "$CERT" ] && tem_cmd openssl; then
      VENC=$(openssl x509 -enddate -noout -in "$CERT" 2>/dev/null | cut -d= -f2)
      echo "  - $NOME: vence em $VENC"
    fi
  done
else
  echo "  Nenhum certificado Let's Encrypt encontrado em /etc/letsencrypt/live."
  echo "  >> Se o site usa HTTPS, confirmar onde o certificado está (proxy externo, Cloudflare, outro caminho)."
fi
linha

# ---------- CRON E AUTOMAÇÃO ----------
echo "CRON E TAREFAS AGENDADAS"
echo "  Crontab do usuário atual:"
crontab -l 2>/dev/null | grep -v '^#' | grep -v '^$' | sed 's/^/    /' || echo "    (vazio ou sem permissão)"
echo "  /etc/cron.d/:"
find /etc/cron.d -maxdepth 1 -type f 2>/dev/null | sed 's/^/    /'
echo "  Timers systemd ativos:"
tem_cmd systemctl && systemctl list-timers --no-pager 2>/dev/null | tail -n +2 | head -15 | sed 's/^/    /'
linha

# ---------- USUÁRIOS E ACESSO ----------
echo "USUÁRIOS E ACESSO SSH"
echo "  Usuários com shell de login válido:"
grep -E '/(bash|sh|zsh)$' /etc/passwd 2>/dev/null | cut -d: -f1 | sed 's/^/    /'
echo "  Usuários com sudo (grupo sudo/wheel):"
getent group sudo wheel 2>/dev/null | cut -d: -f4 | tr ',' '\n' | grep -v '^$' | sed 's/^/    /'
if [ -f /etc/ssh/sshd_config ]; then
  echo "  Config SSH relevante:"
  grep -E '^(PermitRootLogin|PasswordAuthentication|Port)' /etc/ssh/sshd_config 2>/dev/null | sed 's/^/    /'
  ROOT_LOGIN=$(grep -E '^PermitRootLogin' /etc/ssh/sshd_config 2>/dev/null | awk '{print $2}')
  [ "$ROOT_LOGIN" = "yes" ] && echo "  >> ALERTA: PermitRootLogin=yes — login root direto por senha é risco alto."
fi

# Chaves autorizadas
if [ -f "$HOME/.ssh/authorized_keys" ]; then
  echo "  Chaves em authorized_keys:"
  ssh-keygen -lf "$HOME/.ssh/authorized_keys" 2>/dev/null | sed 's/^/    /' || echo "    (não foi possível ler)"
fi

# Autenticação por certificado — vetor que NÃO aparece no authorized_keys
CA_CONF=$(grep -rhiE '^\s*(TrustedUserCAKeys|AuthorizedPrincipalsFile)' \
          /etc/ssh/sshd_config /etc/ssh/sshd_config.d/*.conf 2>/dev/null || true)
if [ -n "$CA_CONF" ]; then
  echo "  >> ATENÇÃO: autenticação por CERTIFICADO configurada:"
  echo "$CA_CONF" | sed 's/^/    /'
  CA_FILE=$(echo "$CA_CONF" | grep -i TrustedUserCAKeys | awk '{print $2}' | head -1)
  if [ -n "$CA_FILE" ] && [ -f "$CA_FILE" ]; then
    echo "    Autoridades certificadoras confiáveis:"
    ssh-keygen -lf "$CA_FILE" 2>/dev/null | sed 's/^/      /'
  fi
  [ -d /etc/ssh/auth_principals ] && \
    echo "    Principals autorizados: $(ls /etc/ssh/auth_principals 2>/dev/null | tr '\n' ' ')"
  echo "  >> Quem tiver certificado assinado por essas CAs entra SEM constar no"
  echo "     authorized_keys. Limpar aquele arquivo não fecha este caminho."
fi

# Quais chaves realmente foram usadas (o log responde o que a lista não responde)
LOGSEC=""
[ -f /var/log/secure ] && LOGSEC="/var/log/secure*"
[ -f /var/log/auth.log ] && LOGSEC="/var/log/auth.log*"
if [ -n "$LOGSEC" ]; then
  echo "  Chaves com login bem-sucedido (janela de retenção do log):"
  grep -h "Accepted publickey" $LOGSEC 2>/dev/null | awk '{print $NF}' \
    | sort | uniq -c | sort -rn | head -10 | sed 's/^/    /' || echo "    (sem registros)"
  echo "  >> 'Sem uso' aqui vale só para o período retido no log — confirme"
  echo "     até onde ele vai antes de concluir que uma chave é morta."
fi
linha

echo "FIM DA AUDITORIA. Isto é um inventário — não corrige nada."
echo "Itens marcados '>> ALERTA' ou '>>' merecem confirmação com o responsável antes de qualquer mudança."

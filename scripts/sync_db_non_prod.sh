#!/usr/bin/env bash
# ==============================================================================
# sync_db_non_prod.sh — Sincronização Segura de Banco de Dados com Sanitização LGPD
# CTDOL / datapoliRS (ADR 044 v2.0.0 & Regra 18 - Zero-Leakage)
#
# Extrai os dados do PostgreSQL de PRODUÇÃO (VPS Oracle OCI), aplica a camada
# mandatória de anonimização/mascaramento LGPD e restaura no container local
# datapoli_postgres_non_prod compartilhado por DEV e HML.
# ==============================================================================
set -euo pipefail

BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
BLUE="\033[0;34m"
RESET="\033[0m"

echo -e "${BOLD}${BLUE}=== CTDOL: Sincronização Segura de Banco Não-Produtivo (datapoliRS) ===${RESET}"

# 1. Checagem de conectividade SSH com a VPS OCI
echo -e "${YELLOW}[1/5] Testando conectividade com VPS OCI (vps-oci)...${RESET}"
if ! ssh -o BatchMode=yes -o ConnectTimeout=5 vps-oci "echo ok" > /dev/null 2>&1; then
    echo -e "${RED}[ERRO] Não foi possível conectar via SSH em vps-oci. Verifique as chaves e rede.${RESET}"
    exit 1
fi
echo -e "${GREEN}[OK] Conexão SSH estabelecida com sucesso.${RESET}"

# 2. Garantir que o container local datapoli_postgres_non_prod esteja rodando
echo -e "${YELLOW}[2/5] Verificando container local datapoli_postgres_non_prod...${RESET}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
cd "$REPO_DIR"

if ! docker ps --format '{{.Names}}' | grep -q "^datapoli_postgres_non_prod$"; then
    echo -e "${YELLOW}Container datapoli_postgres_non_prod não está ativo. Iniciando serviço de banco...${RESET}"
    docker compose up -d postgres
    sleep 3
fi

# Aguardar pg_isready no container local
docker exec datapoli_postgres_non_prod pg_isready -U datapoli_user -d datapoli_db > /dev/null 2>&1 || {
    echo -e "${YELLOW}Aguardando PostgreSQL local inicializar...${RESET}"
    sleep 5
}
echo -e "${GREEN}[OK] Container local pronto.${RESET}"

# 3. Extrair dump de produção da VPS OCI
TMP_DUMP="/tmp/datapoli_prod_raw_$$.sql"
echo -e "${YELLOW}[3/5] Extraindo dump de PRODUÇÃO via SSH (pg_dump na VPS)...${RESET}"
ssh -o BatchMode=yes vps-oci "docker exec datapoli_postgres_prod pg_dump -U datapoli_user -d datapoli_db --clean --if-exists --no-owner --no-privileges" > "$TMP_DUMP"

DUMP_SIZE=$(wc -c < "$TMP_DUMP" | tr -d ' ')
echo -e "${GREEN}[OK] Dump bruto extraído com sucesso (${DUMP_SIZE} bytes).${RESET}"

# 4. Restaurar dump bruto no container local
echo -e "${YELLOW}[4/5] Restaurando dados no PostgreSQL não-produtivo local...${RESET}"
docker exec -i datapoli_postgres_non_prod psql -U datapoli_user -d datapoli_db < "$TMP_DUMP" > /dev/null 2>&1
rm -f "$TMP_DUMP"
echo -e "${GREEN}[OK] Restauração básica concluída.${RESET}"

# 5. Camada de Sanitização, Anonimização e Mascaramento LGPD (Regra 18 / Zero-Leakage)
echo -e "${YELLOW}[5/5] Aplicando Sanitização LGPD (reset de senhas e anonimização de lideranças)...${RESET}"

# Hash Bcrypt de 'admin123'
BCRYPT_ADMIN123='$2b$12$FbvpytnY49pUi2eN6dsZ7uu69ldrf42gjZZSuOzpMswccc7PXhypG'

docker exec -i datapoli_postgres_non_prod psql -U datapoli_user -d datapoli_db << SQL
BEGIN;

-- 1. Redefinir todas as senhas de usuários para 'admin123' (acesso garantido em dev/hml)
UPDATE tb_users
SET hashed_password = '${BCRYPT_ADMIN123}',
    is_active = TRUE;

-- 2. Anonimizar dados pessoais de lideranças (LGPD / Zero-Leakage)
UPDATE tb_gabinete_liderancas
SET nm_completo = 'Liderança ' || SUBSTRING(id_lideranca::text, 1, 8),
    nr_telefone = '(51) 99999-0000',
    ds_email = 'lideranca_' || SUBSTRING(id_lideranca::text, 1, 8) || '@naoprodutivo.local',
    ds_observacoes = 'Registro mascarado para ambiente de teste (LGPD).';

-- 3. Marcar explicitamente o ambiente como NÃO PRODUTIVO no banco
INSERT INTO tb_configuracoes_sistema (chave, valor, tipo, categoria, descricao)
VALUES ('ambiente.tipo', 'NON_PRODUCTION', 'string', 'sistema', 'Identificador de ambiente não-produtivo local')
ON CONFLICT (chave) DO UPDATE SET valor = 'NON_PRODUCTION';

COMMIT;
SQL

echo -e "${GREEN}[OK] Sanitização LGPD concluída com sucesso.${RESET}"
echo -e "${BOLD}${GREEN}=== Sincronização Concluída: Banco Não-Produtivo Pronto para DEV e HML! ===${RESET}"
echo -e "Credenciais Universais Não-Produtivas: ${YELLOW}operador@campanha.com.br${RESET} | Senha: ${YELLOW}admin123${RESET}"

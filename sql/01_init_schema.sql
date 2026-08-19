-- ==============================================================================
-- SCRIPT DE INICIALIZAÇÃO DDL — datapoliRS (PostgreSQL 16 + PostGIS 3.4)
-- ==============================================================================

-- 1. Extensões Essenciais
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";
CREATE EXTENSION IF NOT EXISTS "unaccent";

-- 2. Tabela de Eleições / Pleitos Eleitorais
CREATE TABLE IF NOT EXISTS tb_eleicoes (
    cd_eleicao VARCHAR(20) PRIMARY KEY,
    ano_eleicao INT NOT NULL,
    nr_turno INT NOT NULL DEFAULT 1,
    tp_abrangencia VARCHAR(10) NOT NULL, -- 'E' (Estadual), 'F' (Federal), 'M' (Municipal)
    ds_eleicao VARCHAR(150) NOT NULL,
    dt_eleicao DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_eleicoes_ano ON tb_eleicoes(ano_eleicao);

-- 3. Tabela de Municípios (com Geometria Geoespacial PostGIS)
CREATE TABLE IF NOT EXISTS tb_municipios (
    cd_ibge_7 VARCHAR(7) PRIMARY KEY,
    cd_tse VARCHAR(10) UNIQUE,
    nm_municipio VARCHAR(150) NOT NULL,
    sg_uf CHAR(2) NOT NULL DEFAULT 'RS',
    geometria GEOMETRY(MultiPolygon, 4326),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_municipios_geom ON tb_municipios USING GIST(geometria);
CREATE INDEX IF NOT EXISTS idx_municipios_nome ON tb_municipios(nm_municipio);
CREATE INDEX IF NOT EXISTS idx_municipios_tse ON tb_municipios(cd_tse);

-- 4. Tabela de Partidos Políticos
CREATE TABLE IF NOT EXISTS tb_partidos (
    nr_partido INT PRIMARY KEY,
    sg_partido VARCHAR(20) NOT NULL,
    nm_partido VARCHAR(150) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_partidos_sigla ON tb_partidos(sg_partido);

-- 5. Tabela de Cargos Eletivos
CREATE TABLE IF NOT EXISTS tb_cargos (
    cd_cargo INT PRIMARY KEY,
    ds_cargo VARCHAR(100) NOT NULL
);

-- 6. Tabela de Candidaturas (Dados Oficiais TSE)
CREATE TABLE IF NOT EXISTS tb_candidaturas (
    sq_candidato BIGINT PRIMARY KEY,
    id_tse BIGINT,
    cd_eleicao VARCHAR(20) NOT NULL REFERENCES tb_eleicoes(cd_eleicao),
    cd_cargo INT NOT NULL REFERENCES tb_cargos(cd_cargo),
    nr_candidato INT NOT NULL,
    nm_candidato VARCHAR(255) NOT NULL,
    nm_urna_candidato VARCHAR(150) NOT NULL,
    nr_partido INT NOT NULL REFERENCES tb_partidos(nr_partido),
    sg_uf CHAR(2) NOT NULL DEFAULT 'RS',
    ds_situacao_candidatura VARCHAR(50),
    ds_detalhe_situacao VARCHAR(100),
    st_reeleicao BOOLEAN DEFAULT FALSE,
    vl_total_bens NUMERIC(15, 2) DEFAULT 0.00,
    foto_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_cand_numero_eleicao ON tb_candidaturas(nr_candidato, cd_eleicao);
CREATE INDEX IF NOT EXISTS idx_cand_nome_urna ON tb_candidaturas(nm_urna_candidato);
CREATE INDEX IF NOT EXISTS idx_cand_partido ON tb_candidaturas(nr_partido);

-- 7. Tabela de Bens Declarados
CREATE TABLE IF NOT EXISTS tb_bens_candidatos (
    id_bem UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sq_candidato BIGINT NOT NULL REFERENCES tb_candidaturas(sq_candidato) ON DELETE CASCADE,
    ds_tipo_bem VARCHAR(150),
    ds_detalhe_bem TEXT,
    vl_declarado NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_bens_sq_candidato ON tb_bens_candidatos(sq_candidato);

-- 8. Tabela de Fatos de Votação Nominal por Município e Zona Eleitoral
CREATE TABLE IF NOT EXISTS tb_fato_votacao_munzona (
    id_fato BIGSERIAL PRIMARY KEY,
    cd_eleicao VARCHAR(20) NOT NULL REFERENCES tb_eleicoes(cd_eleicao),
    sq_candidato BIGINT NOT NULL REFERENCES tb_candidaturas(sq_candidato),
    cd_tse_municipio VARCHAR(10) NOT NULL,
    cd_ibge_7 VARCHAR(7) REFERENCES tb_municipios(cd_ibge_7),
    nr_zona INT NOT NULL,
    qt_votos_nominais INT NOT NULL DEFAULT 0,
    qt_votos_validos INT NOT NULL DEFAULT 0,
    CONSTRAINT unq_eleicao_cand_mun_zona UNIQUE (cd_eleicao, sq_candidato, cd_tse_municipio, nr_zona)
);
CREATE INDEX IF NOT EXISTS idx_fato_cand_mun ON tb_fato_votacao_munzona(sq_candidato, cd_tse_municipio);
CREATE INDEX IF NOT EXISTS idx_fato_ibge ON tb_fato_votacao_munzona(cd_ibge_7);

-- 9. Tabela de Gabinete e Lideranças (Multi-Tenancy Obrigatório)
CREATE TABLE IF NOT EXISTS tb_gabinete_liderancas (
    id_lideranca UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL, -- Identificador obrigatório do Gabinete/Mandato
    cd_ibge_7 VARCHAR(7) REFERENCES tb_municipios(cd_ibge_7),
    nm_completo VARCHAR(255) NOT NULL,
    nr_telefone VARCHAR(30),
    ds_email VARCHAR(255),
    tp_influencia VARCHAR(50), -- Ex: 'Comunitária', 'Religiosa', 'Sindical', 'Empresarial'
    ds_observacoes TEXT,
    is_ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_liderancas_tenant ON tb_gabinete_liderancas(tenant_id);
CREATE INDEX IF NOT EXISTS idx_liderancas_municipio ON tb_gabinete_liderancas(cd_ibge_7);

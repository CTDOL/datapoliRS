# Geolocalização de IPs (MaxMind GeoLite2)

Guia operacional da localização de IPs usada no painel SOC (`/plataforma/observabilidade`). A decisão está na ADR 040 (cofre) e o conhecimento técnico vem do fichamento MaxMind do acervo do cofre.

## Por que base local

A localização usa o arquivo `GeoLite2-City.mmdb` lido no próprio servidor. Nenhum IP é enviado a terceiros, o que evita transferência de dados pessoais e a necessidade de contrato de tratamento com um serviço externo. A consulta é em memória e não depende de rede.

## Como funciona

1. O serviço `geoipupdate` (imagem oficial da MaxMind, fixada por digest) baixa a base para o volume `datapolirs_geoip_data` e repete o download a cada `GEOIPUPDATE_FREQUENCY` horas.
2. O download é gravado de forma atômica (troca do arquivo por `rename`), então a API nunca lê um arquivo pela metade.
3. A API monta o volume somente leitura (`:ro`) e lê o caminho em `GEOIP_DB_PATH`.
4. IPs privados (`10.x`, `172.16.x` a `172.31.x`, `192.168.x`, `127.x`) não existem na base pública. O painel mostra "sem localização" e não gera erro.

## Credenciais

Uma conta gratuita na MaxMind fornece `GEOIPUPDATE_ACCOUNT_ID` e `GEOIPUPDATE_LICENSE_KEY`.

- Ficam **somente** no arquivo `.env` (dev) e no `.env` do servidor (produção). O `.env` está no `.gitignore`.
- Nunca colocar a chave em `.env.example`, em commit, em issue ou em log.
- Se a chave vazar, revogar na conta MaxMind e gerar outra. Depois, atualizar a base (comando abaixo).

## Comandos

Dev (na raiz do repositório):

```bash
docker compose run --rm geoipupdate
```

Produção (no servidor):

```bash
docker compose -f docker-compose.prod.yml up -d geoipupdate
```

Verificação rápida no dev:

```bash
docker exec datapoli_api_dev python -c "from app.services.observabilidade_service import localizar as l; print(l('8.8.8.8'), l('172.22.0.1'))"
```

Resultado esperado: `United States None`.

## Atribuição (obrigatória na apresentação e em produção)

O GeoLite2 é distribuído sob a licença da MaxMind, que exige a atribuição de origem. Antes de publicar a tela, confirmar o texto exato no contrato da MaxMind e incluí-lo no rodapé do painel. Texto de referência usado pela MaxMind: "This product includes GeoLite2 data created by MaxMind, available from https://www.maxmind.com".

Status: **incluída** no rodapé de `/plataforma/observabilidade` (dev). Confirmar o texto exato no contrato da MaxMind antes da apresentação.

## Pontos de atenção

- **Frequência:** a base GeoLite2 é atualizada às terças e sextas. Configurado `GEOIPUPDATE_FREQUENCY=24` (ADR 040, Adendo II), no dev e no compose de produção.
- **Precisão:** a localização é aproximada. Pode indicar a cidade ou apenas o país, e as coordenadas são do centro da região. Não usar para identificar pessoas, apenas para contexto de segurança.
- **Imagem:** o compose usa `maxmindinc/geoipupdate` fixada por digest. O fichamento do acervo cita `ghcr.io/maxmind/geoipupdate`. As duas referências são da MaxMind; manter a fixada por digest até conferir a equivalência.
- **Base de teste:** os testes usam uma base de exemplo da MaxMind instalada na máquina do desenvolvedor. Sem ela, os testes de localização são ignorados (`skip`), não falham.

## Referências

- Operação e formato MMDB: fichamento "MaxMind GeoIP e GeoLite — Cap. 1" no acervo destilado do cofre.
- Decisão de arquitetura: ADR 040, Observabilidade, Logs de Acesso e Painel SOC (cofre, `DATAPOLIRS/DOC_OF-datapolirs/`).

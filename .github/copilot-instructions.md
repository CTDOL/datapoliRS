# Contexto do Projeto: API Deputadas Estaduais RS

## Visão Geral
Microsserviço assíncrono em Python (FastAPI) para busca, normalização e consulta de candidaturas a Deputada Estadual no Rio Grande do Sul (RS) via DivulgaCandContas (TSE).

## Diretrizes de Arquitetura e Código
1. Arquitetura em camadas:
   - `app/schemas/`: Modelos de validação Pydantic v2.
   - `app/services/`: Lógica de extração e requisições HTTP assíncronas.
   - `app/main.py`: Endpoints FastAPI, monitoramento e injeção de dependência.
2. Tipagem Estrita: Uso obrigatório de type hints em todas as assinaturas e retornos.
3. Assincronismo e I/O: Chamadas externas executadas via `httpx.AsyncClient` com timeout obrigatório de 10s.
4. Resiliência: Tratamento de exceções com status semânticos (404 para não localizado, 502 para falha na API externa).
5. Compatibilidade de Hospedagem: O servidor deve respeitar a variável de ambiente `PORT` injetada por provedores PaaS (como Render) utilizando fallback padrão para 8000.

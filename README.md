# API Deputadas Estaduais RS

Microsserviço assíncrono em FastAPI para consulta e normalização de candidaturas estaduais via DivulgaCandContas (TSE).

## Como Rodar no Render (Deploy com 1 Clique)
1. Suba este projeto para um repositório no seu GitHub.
2. Acesse o painel do [Render](https://render.com) e clique em **New** > **Blueprint**.
3. Conecte o repositório. O Render lerá o arquivo `render.yaml` automaticamente, instalará as dependências e iniciará o servidor na porta correta (`$PORT`).

## Execução no GitHub Codespaces
1. No seu repositório GitHub, clique em **Code** > **Codespaces** > **Create codespace on main**.
2. No terminal integrado do Codespaces:
   ```bash
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000
   ```
3. O Codespaces abrirá a porta `8000` automaticamente com acesso ao Swagger em `/docs`.

## Execução Local
```bash
python -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

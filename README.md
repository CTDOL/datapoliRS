# 🦅 DataPoliRS 

> **Inteligência Eleitoral que não trava, não cai e não custa uma fortuna em servidores.**

Esqueça as planilhas de 2GB que fritam o seu computador. O **DataPoliRS** é uma prova de conceito disruptiva de análise de dados eleitorais. Nós pegamos a base de dados massiva do Tribunal Superior Eleitoral (TSE), mastigamos, e entregamos uma experiência visual de altíssimo desempenho, rodando lisa em servidores gratuitos.

## 🚀 O que fazemos de diferente?

O modelo tradicional de análise de dados públicos exige baixar gigabytes de CSVs, subir bancos de dados caros em nuvem e rezar para a API do governo não cair. Nós viramos o jogo:

1. **Proxy Híbrido:** Usamos o FastAPI em Python para consumir as informações cadastrais leves da API `DivulgaCandContas` em tempo real.
2. **Micro-Database Estático:** Transformamos 150MB de arquivos brutos de votação de 2022 em um arquivo JSON cirúrgico de apenas 7MB.
3. **Mapas Coropléticos Instantâneos:** Injetamos essa inteligência no frontend com `Leaflet.js`, renderizando redutos eleitorais e mapas de calor no navegador do usuário em milissegundos.

## 🛠️ Stack Tecnológica

- **Backend:** Python + FastAPI (Assíncrono, tipado, ultrarrápido).
- **Processamento de Dados:** Pandas (Scripts isolados para extração e limpeza do TSE).
- **Frontend:** Vanilla HTML/JS + CSS (Glassmorphism e design moderno).
- **Inteligência Geográfica:** Leaflet.js + GeoJSON do IBGE/Github.

## 🕹️ Como rodar essa belezinha na sua máquina

Certifique-se de ter o Python 3.9+ instalado.

```bash
# 1. Clone o repositório
git clone https://github.com/CTDOL/datapoliRS.git
cd datapoliRS

# 2. Crie e ative um ambiente virtual
python -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Inicie o servidor
uvicorn app.main:app --reload
```

Acesse `http://localhost:8000` no seu navegador e sinta a velocidade.

## 🗺️ Como atualizar os Mapas de Votos?

Para gerar a base de dados do zero (você não precisa fazer isso para rodar o app, pois o JSON minificado já está no repo):

```bash
python scripts/processar_votos.py
```
Esse script vai baixar os resultados oficiais do TSE, cruzar os dados, somar os votos por município e gerar o arquivo hiper-compactado `votos_rs_2022.json`.

---
*Construído com sangue, suor e Inteligência Artificial. Democratizando o acesso à informação política de forma elegante.*

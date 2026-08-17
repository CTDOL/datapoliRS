import os
import urllib.request
import zipfile
import pandas as pd
import json

URL = "https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_candidato_munzona/votacao_candidato_munzona_2022.zip"
ZIP_FILE = "votacao.zip"
CSV_FILE = "votacao_candidato_munzona_2022_RS.csv"
OUTPUT_FILE = "app/data/votos_rs_2022.json"

def main():
    if not os.path.exists("app/data"):
        os.makedirs("app/data")

    if not os.path.exists(ZIP_FILE) and not os.path.exists(CSV_FILE):
        print(f"Baixando {URL}...")
        urllib.request.urlretrieve(URL, ZIP_FILE)
        print("Download concluido.")

    if not os.path.exists(CSV_FILE):
        print("Extraindo arquivo do RS...")
        with zipfile.ZipFile(ZIP_FILE, 'r') as zip_ref:
            zip_ref.extract(CSV_FILE)
        print("Extracao concluida.")

    print("Processando dados com Pandas...")
    df = pd.read_csv(CSV_FILE, sep=';', encoding='latin1')
    
    df_deputados = df[df['DS_CARGO'] == 'Deputado Estadual']
    
    df_agrupado = df_deputados.groupby(['NR_CANDIDATO', 'NM_MUNICIPIO'])['QT_VOTOS_NOMINAIS'].sum().reset_index()
    
    resultado = {}
    for _, row in df_agrupado.iterrows():
        nr = str(row['NR_CANDIDATO'])
        mun = row['NM_MUNICIPIO']
        votos = int(row['QT_VOTOS_NOMINAIS'])
        
        if nr not in resultado:
            resultado[nr] = {}
        resultado[nr][mun] = votos

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(resultado, f, ensure_ascii=False)
        
    print(f"Arquivo salvo em {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

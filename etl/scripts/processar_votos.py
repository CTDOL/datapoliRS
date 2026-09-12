import argparse
import os
import urllib.request
import zipfile
import pandas as pd
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # etl/
REPO_ROOT = os.path.dirname(BASE_DIR)
DATA_DIR = os.path.join(BASE_DIR, "data")


def main(ano: int):
    url = f"https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_candidato_munzona/votacao_candidato_munzona_{ano}.zip"
    csvName = f"votacao_candidato_munzona_{ano}_RS.csv"
    zipFile = os.path.join(DATA_DIR, f"votacao_{ano}.zip")
    csvFile = os.path.join(DATA_DIR, csvName)
    outputFile = os.path.join(REPO_ROOT, "backend", "app", "data", f"votos_rs_{ano}.json")

    os.makedirs(os.path.dirname(outputFile), exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(zipFile) and not os.path.exists(csvFile):
        print(f"Baixando {url}...")
        urllib.request.urlretrieve(url, zipFile)
        print("Download concluido.")

    if not os.path.exists(csvFile):
        print("Extraindo arquivo do RS...")
        with zipfile.ZipFile(zipFile, 'r') as zip_ref:
            zip_ref.extract(csvName, path=DATA_DIR)
        print("Extracao concluida.")

    print("Processando dados com Pandas...")
    df = pd.read_csv(csvFile, sep=';', encoding='latin1')

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

    with open(outputFile, 'w', encoding='utf-8') as f:
        json.dump(resultado, f, ensure_ascii=False)

    print(f"Arquivo salvo em {outputFile}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agrega votos nominais por candidato/município do TSE (RS, Deputado Estadual).")
    parser.add_argument("--ano", type=int, required=True, help="Ano do pleito a processar (ex.: 2022, 2026).")
    args = parser.parse_args()
    main(args.ano)

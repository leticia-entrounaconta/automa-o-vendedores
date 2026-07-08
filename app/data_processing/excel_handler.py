import os
import logging
from time import time, sleep

import pandas as pd

from app.settings.config import DOWNLOAD_PATH


VENDEDORES_REMOVER = [
    "camila kawai",
    "enc-colaboradores",
    "enc+",
    "improdutivo",
    "não identificado",
    "sem atuação",
]


def wait_download(timeout=60, extension=".xlsx"):
    start_time = time()
    arquivos_antes = set(os.listdir(DOWNLOAD_PATH))

    while time() - start_time < timeout:
        arquivos_agora = set(os.listdir(DOWNLOAD_PATH))
        novos_arquivos = arquivos_agora - arquivos_antes

        arquivos_validos = [
            os.path.join(DOWNLOAD_PATH, arquivo)
            for arquivo in novos_arquivos
            if arquivo.endswith(extension)
            and not arquivo.endswith(".crdownload")
            and not arquivo.endswith(".tmp")
        ]

        if arquivos_validos:
            arquivo_mais_recente = max(arquivos_validos, key=os.path.getctime)

            if check_download(arquivo_mais_recente):
                logging.info(f"Download completed: {arquivo_mais_recente}")
                return arquivo_mais_recente

        sleep(0.5)

    logging.warning(f"Download not completed within {timeout} seconds")
    return None


def check_download(file_path):
    if (
        os.path.exists(file_path)
        and not file_path.endswith(".crdownload")
        and not file_path.endswith(".tmp")
        and os.path.getsize(file_path) > 0
        and _file_is_stable(file_path)
    ):
        return True

    return False


def _file_is_stable(file_path, checks=3, interval=0.5):
    previous_size = -1

    for _ in range(checks):
        if not os.path.exists(file_path):
            return False

        current_size = os.path.getsize(file_path)

        if current_size == 0:
            return False

        if current_size == previous_size:
            return True

        previous_size = current_size
        sleep(interval)

    return True


def clean_excel(file_path):
    try:
        df = pd.read_excel(file_path)

        if df.empty:
            logging.error("A planilha está vazia.")
            return None

        df.columns = df.columns.astype(str).str.strip()

        required_columns = ["GrupoVendedor"]

        missing_columns = [
            column for column in required_columns
            if column not in df.columns
        ]

        if missing_columns:
            logging.error(f"Colunas obrigatórias não encontradas: {missing_columns}")
            logging.error(f"Colunas disponíveis: {list(df.columns)}")
            return None

        coluna_vendedor = "GrupoVendedor"

        df[coluna_vendedor] = (
            df[coluna_vendedor]
            .astype(str)
            .str.strip()
            .str.lower()
        )

        df = df[
            ~df[coluna_vendedor].isin(VENDEDORES_REMOVER)
        ]

        output_path = os.path.join(DOWNLOAD_PATH, "Automacao.xlsx")
        df.to_excel(output_path, index=False)

        logging.info(f"Cleaned Excel file saved to {output_path}")
        return output_path

    except Exception as e:
        logging.error(f"Error cleaning Excel file: {e}")
        return None
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


def wait_download(timeout=10):
    loop = True
    start_time = time()

    while loop:
        elapsed_time = time() - start_time

        try:
            response = check_download(
                os.path.join(DOWNLOAD_PATH, os.listdir(DOWNLOAD_PATH)[0])
            )
            loop = not response

        except IndexError:
            if elapsed_time > timeout:
                break
            else:
                sleep(0.5)

    if loop:
        logging.warning(f"Download not completed within {timeout} seconds")
        return None

    logging.info(f"Download completed, file found in {DOWNLOAD_PATH}")
    return os.path.join(DOWNLOAD_PATH, os.listdir(DOWNLOAD_PATH)[0])


def check_download(file):
    if (
        os.path.exists(file)
        and ".crdownload" not in file
        and ".tmp" not in file
        and os.path.getsize(file) > 0
    ):
        logging.info(f"{file}")
        return True

    return False


def clean_excel(file_path):
    try:
        df = pd.read_excel(file_path)

        df.columns = df.columns.astype(str).str.strip()

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

        file_name = "Automacao"
        output_path = os.path.join(DOWNLOAD_PATH, f"{file_name}.xlsx")

        df.to_excel(output_path, index=False)

        logging.info(f"Cleaned Excel file saved to {output_path}")
        return output_path

    except Exception as e:
        logging.error(f"Error cleaning Excel file: {e}")
        return None
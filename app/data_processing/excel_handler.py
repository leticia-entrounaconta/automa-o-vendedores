import os
import logging
from time import time, sleep
from app.settings.config import DOWNLOAD_PATH
from datetime import datetime

def wait_download(timeout = 10):
    loop = True
    start_time = time()
    while loop:
        elapsed_time = time() - start_time
        try:
            response = check_download(os.path.join(DOWNLOAD_PATH, os.listdir(DOWNLOAD_PATH)[0]))
            loop = not response
        except IndexError:
            if elapsed_time > timeout:
                break
            else:
                sleep(0.5)
                pass
    if loop:
        logging.warning(f'Download not completed within {timeout} seconds')
        return None
    else:
        logging.info(f'Download completed, file found in {DOWNLOAD_PATH}')
        return os.path.join(DOWNLOAD_PATH, os.listdir(DOWNLOAD_PATH)[0])

def check_download(file):
    if os.path.exists(file) and not ".crdownload" in file and not ".tmp" in file and os.path.getsize(file) > 0:
        logging.info(f'{file}')
        return True
    else:
        return False

def clean_excel(file_path):
    import pandas as pd
    try:
        df = pd.read_excel(file_path)
        # 
        # 
        #                 
        file_name='Automacao'
        output_path = os.path.join(DOWNLOAD_PATH, f"{file_name}.xlsx")
        df.to_excel(output_path, index=False)
        logging.info(f'Cleaned Excel file saved to {output_path}')
        return output_path
    except Exception as e:
        logging.error(f'Error cleaning Excel file: {e}')
        return None
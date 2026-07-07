import logging
from time import sleep

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from app.settings.driver_settings import wait
from app.data_processing.excel_handler import wait_download


logger = logging.getLogger(__name__)


def export_vendedores_ativos():
    logger.info("Abrindo aba Cadastro")

    wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//*[normalize-space()='Cadastro']")
        )
    ).click()

    sleep(1)

    logger.info("Abrindo filtro Situacao de Cadastro")

    wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//*[contains(normalize-space(), 'Situação de Cadastro')]/following::div[contains(@class, 'select')][1]")
        )
    ).click()

    sleep(1)

    logger.info("Selecionando situacao Ativo")

    wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//*[normalize-space()='Ativo']")
        )
    ).click()

    sleep(1)

    logger.info("Pesquisando vendedores ativos")

    wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(normalize-space(), 'Pesquisar')]")
        )
    ).click()

    sleep(2)

    logger.info("Exportando planilha")

    wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(normalize-space(), 'Exportar')]")
        )
    ).click()

    logger.info("Aguardando download")

    file_path = wait_download()

    if not file_path:
        logger.error("Arquivo exportado nao encontrado.")
        return None

    logger.info("Arquivo exportado: %s", file_path)
    return file_path


import logging
from time import sleep

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from app.settings.driver_settings import driver, wait
from app.data_processing.excel_handler import wait_download


logger = logging.getLogger(__name__)


def export_vendedores_ativos():
    logger.info("Abrindo painel de Filtros")

    filtros = wait.until(
        EC.element_to_be_clickable((By.ID, "btnExibeFiltro"))
    )

    driver.execute_script("arguments[0].click();", filtros)

    sleep(1)

    logger.info("Selecionando aba Cadastro")

    cadastro = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//a[@role='tab'][.//h6[normalize-space()='Cadastro']]",
            )
        )
    )

    driver.execute_script("arguments[0].click();", cadastro)

    sleep(1)

    logger.info("Abrindo filtro Situação de Cadastro")

    filtro_situacao = wait.until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "button[data-id='ddlSituacaoVendedor']")
        )
    )

    driver.execute_script("arguments[0].click();", filtro_situacao)

    sleep(1)

    logger.info("Selecionando Ativo")

    ativo = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//span[normalize-space()='Ativo']",
            )
        )
    )

    driver.execute_script("arguments[0].click();", ativo)

    sleep(1)

    logger.info("Pesquisando vendedores")

    pesquisar = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//button[contains(normalize-space(),'Pesquisar')]",
            )
        )
    )

    driver.execute_script("arguments[0].click();", pesquisar)

    sleep(2)

    logger.info("Exportando planilha")

    exportar = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//button[contains(normalize-space(),'Exportar')]",
            )
        )
    )

    driver.execute_script("arguments[0].click();", exportar)

    logger.info("Aguardando download")

    file_path = wait_download()

    if file_path is None:
        logger.error("Arquivo exportado não encontrado.")
        return None

    logger.info("Arquivo exportado: %s", file_path)

    return file_path
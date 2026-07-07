import logging
from functools import wraps
from time import sleep

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from app.settings.config import BASE_URL, BASE_URL_2TECH
from app.settings.driver_settings import driver, wait


logger = logging.getLogger(__name__)


def open_browser(func):
    """Decorator that navigates to BASE_URL before executing the wrapped function."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.info("Navegando para %s", BASE_URL)
        driver.get(BASE_URL)
        return func(*args, **kwargs)

    return wrapper


def navigate_to(url: str):
    """Navigate the browser to a specific URL."""
    logger.info("Navegando para %s", url)
    driver.get(url)


def navigate_to_system():
    logger.info("Navegando para sistema 2Tech")
    driver.get(f"{BASE_URL_2TECH}default.asp")


def switch_to_window(index: int = 0):
    """Switch to a browser window by index."""
    handles = driver.window_handles

    if index < len(handles):
        driver.switch_to.window(handles[index])
        logger.debug("Switched to window %d", index)
    else:
        logger.warning("Window index %d nao existe (total: %d)", index, len(handles))


def navigate_to_cadastros():
    logger.info("Navegando para Cadastros")

    wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//*[contains(normalize-space(), 'Cadastros')]")
        )
    ).click()

    sleep(1)


def navigate_to_vendedores():
    logger.info("Navegando para Vendedores")

    wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//*[contains(normalize-space(), 'Vendedores')]")
        )
    ).click()

    sleep(2)


def open_filter():
    logger.info("Abrindo filtro")

    wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//*[contains(normalize-space(), 'Filtro') or contains(normalize-space(), 'Filtrar')]")
        )
    ).click()

    sleep(1)


def select_cadastro_ativo():
    logger.info("Selecionando cadastro ativo")

    wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//*[contains(normalize-space(), 'Cadastro')]")
        )
    ).click()

    sleep(1)

    wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//*[contains(normalize-space(), 'Ativo')]")
        )
    ).click()

    sleep(1)


def search_vendedores():
    logger.info("Pesquisando vendedores")

    wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//*[contains(normalize-space(), 'Pesquisar')]")
        )
    ).click()

    sleep(2)


def export_vendedores():
    logger.info("Exportando vendedores")

    wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//*[contains(normalize-space(), 'Exportar')]")
        )
    ).click()

    sleep(2)


def return_to_previous_page():
    logger.info("Retornando para pagina anterior")
    driver.back()
    sleep(2)


def run_vendedores_flow():
    logger.info("Iniciando fluxo de vendedores")

    navigate_to_cadastros()
    navigate_to_vendedores()
    open_filter()
    select_cadastro_ativo()
    search_vendedores()
    export_vendedores()

    logger.info("Fluxo de vendedores finalizado")
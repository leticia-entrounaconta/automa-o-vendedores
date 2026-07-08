import logging
from functools import wraps
from time import sleep

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from app.settings.driver_settings import driver, wait


BASE_URL = "https://app1.gerencialcredito.com.br/Entrounaconta/"
BASE_URL_2TECH = "https://app1.gerencialcredito.com.br/Entrounaconta/"

logger = logging.getLogger(__name__)


def open_browser(func):
    """Decorator que navega para BASE_URL antes de executar a função."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.info("Navegando para %s", BASE_URL)
        driver.get(BASE_URL)
        return func(*args, **kwargs)

    return wrapper


def navigate_to(url: str):
    logger.info("Navegando para %s", url)
    driver.get(url)


def navigate_to_system():
    logger.info("Navegando para sistema 2Tech")
    driver.get(f"{BASE_URL_2TECH.rstrip('/')}/default.asp")


def switch_to_window(index: int = 0):
    handles = driver.window_handles

    if index < len(handles):
        driver.switch_to.window(handles[index])
        logger.debug("Switched to window %d", index)
    else:
        logger.warning("Window index %d nao existe. Total: %d", index, len(handles))


def navigate_to_cadastros():
    logger.info("Navegando para Cadastros")

    cadastros = wait.until(
        EC.presence_of_element_located((By.ID, "menu4"))
    )

    driver.execute_script(
        "arguments[0].click();",
        cadastros,
    )

    sleep(1)


def navigate_to_vendedores():
    logger.info("Navegando para Vendedores")

    vendedores = wait.until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "//a[contains(@href, 'BuscarVendedor.asp') and contains(normalize-space(), 'Vendedores')]",
            )
        )
    )

    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'});",
        vendedores,
    )

    sleep(0.5)

    driver.execute_script(
        "arguments[0].click();",
        vendedores,
    )

    sleep(2)


def return_to_previous_page():
    logger.info("Retornando para pagina anterior")
    driver.back()
    sleep(2)
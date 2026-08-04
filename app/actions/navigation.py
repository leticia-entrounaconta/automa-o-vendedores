import logging
from functools import wraps

from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from app.settings.driver_settings import driver, wait
from app.settings.config import BASE_URL, BASE_URL_2TECH

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
    if not BASE_URL_2TECH:
        raise RuntimeError("Configure BASE_URL_2TECH ou URL_2TECH no arquivo .env.")
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

    driver.execute_script(
        "arguments[0].click();",
        vendedores,
    )


def navigate_to_producao_layout(driver, timeout: int = 20) -> None:
    """Acessa Operacional > Produção - Layout na sessão autenticada da 2Tech."""
    wait = WebDriverWait(driver, timeout)

    try:
        logger.info("Acessando o menu Operacional...")
        menu_operacional = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//a[normalize-space(.)='Operacional']")
            )
        )
        try:
            menu_operacional.click()
        except ElementClickInterceptedException:
            logger.info("Menu Operacional exige hover; usando ActionChains.")
            ActionChains(driver).move_to_element(menu_operacional).perform()

        logger.info("Acessando Produção - Layout...")
        producao_layout = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//a[normalize-space(.)='Produção - Layout' "
                    "or normalize-space(.)='Produção – Layout']",
                )
            )
        )
        try:
            producao_layout.click()
        except ElementClickInterceptedException:
            logger.info("Item Produção - Layout exige hover; usando ActionChains.")
            menu_operacional = wait.until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//a[normalize-space(.)='Operacional']")
                )
            )
            ActionChains(driver).move_to_element(menu_operacional).perform()
            producao_layout = wait.until(
                EC.visibility_of_element_located(
                    (
                        By.XPATH,
                        "//a[normalize-space(.)='Produção - Layout' "
                        "or normalize-space(.)='Produção – Layout']",
                    )
                )
            )
            ActionChains(driver).move_to_element(producao_layout).click().perform()

        wait.until(lambda current_driver: "Importacao_Digitacao_Proposta_Lista.asp" in current_driver.current_url)
        logger.info("Tela Produção - Layout acessada com sucesso.")
    except Exception:
        logger.exception("Não foi possível acessar Operacional > Produção - Layout.")
        raise


def return_to_previous_page():
    logger.info("Retornando para pagina anterior")
    driver.back()

"""Explicit waits used across 2Tech Selenium flows."""

from __future__ import annotations

from collections.abc import Iterable

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from app.settings.config import WAIT_PADRAO, WAIT_RELATORIO


def criar_wait(driver, timeout: int = WAIT_PADRAO) -> WebDriverWait:
    return WebDriverWait(driver, timeout)


def esperar_documento_carregar(driver, timeout: int = WAIT_PADRAO) -> None:
    criar_wait(driver, timeout).until(
        lambda current_driver: current_driver.execute_script("return document.readyState") == "complete"
    )


def esperar_elemento_visivel(driver, locator, timeout: int = WAIT_PADRAO):
    return criar_wait(driver, timeout).until(EC.visibility_of_element_located(locator))


def esperar_elemento_clicavel(driver, locator, timeout: int = WAIT_PADRAO):
    return criar_wait(driver, timeout).until(EC.element_to_be_clickable(locator))


def esperar_loading_desaparecer(
    driver,
    locators: Iterable[tuple[str, str]],
    timeout: int = WAIT_RELATORIO,
) -> None:
    """Wait only for known overlays that are actually present on the screen."""
    wait = criar_wait(driver, timeout)
    for locator in locators:
        wait.until(EC.invisibility_of_element_located(locator))


def esperar_tabela_carregar(driver, locator, timeout: int = WAIT_RELATORIO):
    """Wait for a visible table containing at least one row in tbody."""
    def table_has_rows(current_driver):
        table = current_driver.find_element(*locator)
        return table if table.is_displayed() and table.find_elements("css selector", "tbody tr") else False

    return criar_wait(driver, timeout).until(table_has_rows)

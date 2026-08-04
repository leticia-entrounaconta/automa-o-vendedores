"""Reliable, observable Selenium clicks with bounded retries."""

from __future__ import annotations

import logging

from selenium.common.exceptions import ElementClickInterceptedException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains

from app.browser.exceptions import AutomationError
from app.browser.waits import esperar_elemento_clicavel, esperar_elemento_visivel
from app.settings.config import MAX_TENTATIVAS, WAIT_PADRAO
from app.utils.evidencias import registrar_evidencia_erro

logger = logging.getLogger(__name__)


def clicar_elemento(
    driver,
    wait,
    locator,
    descricao: str,
    usar_javascript_fallback: bool = True,
) -> None:
    """Click an element with normal, ActionChains and JS fallback strategies."""
    last_error: Exception | None = None
    timeout = int(getattr(wait, "_timeout", WAIT_PADRAO))
    for tentativa in range(1, MAX_TENTATIVAS + 1):
        try:
            logger.info("%s | clique | tentativa=%d/%d", descricao, tentativa, MAX_TENTATIVAS)
            element = esperar_elemento_visivel(driver, locator, timeout)
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            element = esperar_elemento_clicavel(driver, locator, timeout)
            try:
                element.click()
                logger.info("%s | clique normal concluído", descricao)
                return
            except ElementClickInterceptedException:
                ActionChains(driver).move_to_element(element).click().perform()
                logger.info("%s | clique ActionChains concluído", descricao)
                return
        except (ElementClickInterceptedException, WebDriverException) as error:
            last_error = error
            logger.warning("%s | clique falhou | tentativa=%d | erro=%s", descricao, tentativa, error)

    if usar_javascript_fallback:
        try:
            element = esperar_elemento_visivel(driver, locator, timeout)
            driver.execute_script("arguments[0].click();", element)
            logger.info("%s | clique JavaScript concluído", descricao)
            return
        except WebDriverException as error:
            last_error = error

    evidence = registrar_evidencia_erro(driver, descricao, locator, last_error)
    raise AutomationError(f"Falha ao clicar em '{descricao}'. Evidências: {evidence}") from last_error


def clicar_primeiro_disponivel(
    driver,
    wait,
    locators: tuple[tuple[str, str], ...],
    descricao: str,
) -> tuple[str, str]:
    """Try selector alternatives in order and return the one that succeeded."""
    last_error: Exception | None = None
    for locator in locators:
        try:
            clicar_elemento(driver, wait, locator, descricao)
            logger.info("%s | seletor selecionado=%s", descricao, locator)
            return locator
        except AutomationError as error:
            last_error = error
    raise AutomationError(f"Nenhum seletor funcionou para '{descricao}'.") from last_error

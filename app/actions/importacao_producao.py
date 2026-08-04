"""Rotina opcional de importação para Produção - Layout.

Este módulo é deliberadamente separado da exportação do Relatório Geral para
evitar que um fluxo de download abra ou envie arquivos por engano.
"""

from __future__ import annotations

import logging
from pathlib import Path

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait

from app.browser.clicks import clicar_elemento
from app.settings.driver_settings import driver as default_driver
from app.settings.selectors import ImportacaoProducaoSelectors

logger = logging.getLogger(__name__)


def _preencher_campo(driver, wait, locator, value: str) -> None:
    field = wait.until(EC.visibility_of_element_located(locator))
    field.clear()
    field.send_keys(value)
    driver.execute_script(
        "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
        field,
    )


def clicar_importar_arquivo(driver=default_driver, timeout: int = 20) -> None:
    """Abre o modal de importação sem enviar nenhum arquivo."""
    wait = WebDriverWait(driver, timeout)
    logger.info("importação | abrindo modal de arquivo")
    clicar_elemento(
        driver,
        wait,
        ImportacaoProducaoSelectors.IMPORT_FILE_BUTTON,
        "importacao_producao_abrir_modal",
    )
    wait.until(EC.visibility_of_element_located(ImportacaoProducaoSelectors.IMPORT_FILE_MODAL))


def importar_arquivo_producao(
    caminho_arquivo: Path,
    layout: str,
    correspondente: str | None = None,
    banco: str | None = None,
    data_inicial: str | None = None,
    data_final: str | None = None,
    tipo_data: str | None = None,
    driver=default_driver,
    timeout: int = 20,
) -> None:
    """Envia um arquivo somente quando chamada explicitamente pelo consumidor."""
    arquivo = Path(caminho_arquivo).resolve()
    if not arquivo.is_file():
        raise FileNotFoundError(f"Arquivo de produção não encontrado: {arquivo}")

    wait = WebDriverWait(driver, timeout)
    try:
        clicar_importar_arquivo(driver, timeout)
        wait.until(
            EC.frame_to_be_available_and_switch_to_it(
                ImportacaoProducaoSelectors.IMPORT_FILE_IFRAME
            )
        )
        logger.info("importação | selecionando arquivo=%s", arquivo.name)
        wait.until(
            EC.presence_of_element_located(ImportacaoProducaoSelectors.IMPORT_FILE_INPUT)
        ).send_keys(str(arquivo))

        if correspondente:
            Select(
                wait.until(
                    EC.element_to_be_clickable(ImportacaoProducaoSelectors.IMPORT_CORRESPONDENTE)
                )
            ).select_by_visible_text(correspondente)
        Select(
            wait.until(EC.element_to_be_clickable(ImportacaoProducaoSelectors.IMPORT_LAYOUT))
        ).select_by_visible_text(layout)
        if banco:
            Select(
                wait.until(EC.element_to_be_clickable(ImportacaoProducaoSelectors.IMPORT_BANCO))
            ).select_by_visible_text(banco)
        if data_inicial:
            _preencher_campo(
                driver,
                wait,
                ImportacaoProducaoSelectors.IMPORT_DATA_INICIAL,
                data_inicial,
            )
        if data_final:
            _preencher_campo(
                driver,
                wait,
                ImportacaoProducaoSelectors.IMPORT_DATA_FINAL,
                data_final,
            )
        if tipo_data:
            Select(
                wait.until(
                    EC.presence_of_element_located(
                             ProducaoSelectors.RELATORIO_TIPO_DATA
                    )
                )
            ).select_by_visible_text(tipo_data)

        logger.info("importação | enviando arquivo=%s", arquivo.name)
        clicar_elemento(
            driver,
            wait,
            ImportacaoProducaoSelectors.IMPORT_SUBMIT_BUTTON,
            "importacao_producao_enviar_arquivo",
        )
    except Exception:
        logger.exception("importação | falha ao enviar arquivo=%s", arquivo.name)
        raise
    finally:
        driver.switch_to.default_content()

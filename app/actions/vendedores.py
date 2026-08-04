"""Selenium flow for the existing active-seller export."""

from __future__ import annotations

import logging
from pathlib import Path

from app.browser.clicks import clicar_elemento
from app.browser.exceptions import DownloadError
from app.data_processing.excel_handler import snapshot_downloads, wait_download
from app.utils.evidencias import registrar_evidencia_erro
from app.settings.driver_settings import driver as default_driver
from app.settings.driver_settings import wait as default_wait
from app.settings.selectors import VendedoresSelectors

logger = logging.getLogger(__name__)


def exportar_vendedores_ativos(driver=default_driver, wait=default_wait) -> Path:
    """Apply the Active status filter and return the exact new download path."""
    try:
        logger.info("vendedores | exportação iniciada")
        clicar_elemento(driver, wait, VendedoresSelectors.FILTERS_BUTTON, "vendedores_abrir_filtros")
        clicar_elemento(driver, wait, VendedoresSelectors.CADASTRO_TAB, "vendedores_aba_cadastro")
        clicar_elemento(driver, wait, VendedoresSelectors.SITUACAO_DROPDOWN, "vendedores_filtro_situacao")
        clicar_elemento(driver, wait, VendedoresSelectors.ATIVO_OPTION, "vendedores_selecionar_ativo")
        clicar_elemento(driver, wait, VendedoresSelectors.SEARCH_BUTTON, "vendedores_consultar")

        files_before_export = snapshot_downloads()
        clicar_elemento(driver, wait, VendedoresSelectors.EXPORT_BUTTON, "vendedores_exportar")
        downloaded_file = wait_download(files_before_export)
        logger.info("vendedores | download concluído | arquivo=%s", downloaded_file)
        return downloaded_file
    except DownloadError as error:
        evidence = registrar_evidencia_erro(driver, "vendedores_download", erro=error)
        raise DownloadError(f"Falha no download de vendedores. Evidências: {evidence}") from error

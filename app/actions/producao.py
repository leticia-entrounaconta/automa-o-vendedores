from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait

from app.browser.clicks import clicar_elemento
from app.browser.exceptions import DownloadError, ExportError
from app.browser.waits import (
    esperar_documento_carregar,
    esperar_loading_desaparecer,
    esperar_tabela_carregar,
)
from app.data_processing.excel_handler import (
    snapshot_downloads,
    wait_download,
)
from app.settings.config import (
    RELATORIO_PRODUCAO_URL,
    WAIT_RELATORIO,
    get_periodo_producao,
)
from app.settings.driver_settings import driver as default_driver
from app.settings.selectors import ProducaoSelectors
from app.utils.evidencias import registrar_evidencia_erro


logger = logging.getLogger(__name__)


def _converter_data_para_iso(value: str) -> str:
    """Converte uma data para o formato aceito por input type=date.

    Formatos aceitos:

    - DD/MM/AAAA;
    - AAAA-MM-DD.
    """

    formatos_aceitos = (
        "%d/%m/%Y",
        "%Y-%m-%d",
    )

    for formato in formatos_aceitos:
        try:
            data_convertida = datetime.strptime(
                value,
                formato,
            )

            return data_convertida.strftime(
                "%Y-%m-%d"
            )

        except ValueError:
            continue

    raise ExportError(
        f"Data inválida para o relatório: {value!r}. "
        "Use DD/MM/AAAA ou AAAA-MM-DD."
    )


def _garantir_painel_datas(
    driver: Any,
    wait: WebDriverWait,
) -> None:
    """Aguarda os campos principais do painel Datas."""

    logger.info(
        "produção | aguardando campos do painel Datas"
    )

    data_inicial = wait.until(
        EC.visibility_of_element_located(
            ProducaoSelectors.RELATORIO_DATA_INICIAL
        )
    )

    data_final = wait.until(
        EC.visibility_of_element_located(
            ProducaoSelectors.RELATORIO_DATA_FINAL
        )
    )

    # O select original fica oculto pelo bootstrap-select.
    # Por isso, aguardamos apenas sua presença no HTML.
    tipo_data = wait.until(
        EC.presence_of_element_located(
            ProducaoSelectors.RELATORIO_TIPO_DATA
        )
    )

    if not data_inicial.is_displayed():
        raise ExportError(
            "O campo txtDataInicial existe, "
            "mas não está visível."
        )

    if not data_final.is_displayed():
        raise ExportError(
            "O campo txtDataFinal existe, "
            "mas não está visível."
        )

    logger.info(
        "produção | painel Datas disponível | "
        "data_inicial=%s | data_final=%s | tipo_data=%s",
        data_inicial.get_attribute("id"),
        data_final.get_attribute("id"),
        tipo_data.get_attribute("id"),
    )


def _preencher_data_relatorio(
    driver: Any,
    wait: WebDriverWait,
    locator: tuple[str, str],
    value: str,
    nome_campo: str,
) -> None:
    """Preenche e valida um campo HTML input type=date."""

    value_iso = _converter_data_para_iso(
        value
    )

    quantidade_encontrada = len(
        driver.find_elements(*locator)
    )

    logger.info(
        "produção | procurando campo de data | "
        "campo=%s | locator=%s | url=%s | "
        "titulo=%s | quantidade_encontrada=%d",
        nome_campo,
        locator,
        driver.current_url,
        driver.title,
        quantidade_encontrada,
    )

    field = wait.until(
        EC.visibility_of_element_located(
            locator
        )
    )

    driver.execute_script(
        """
        arguments[0].scrollIntoView({
            block: 'center',
            inline: 'nearest'
        });
        """,
        field,
    )

    driver.execute_script(
        """
        const campo = arguments[0];
        const valor = arguments[1];

        campo.value = '';

        campo.dispatchEvent(
            new Event('input', {
                bubbles: true
            })
        );

        campo.value = valor;

        campo.dispatchEvent(
            new Event('input', {
                bubbles: true
            })
        );

        campo.dispatchEvent(
            new Event('change', {
                bubbles: true
            })
        );

        campo.dispatchEvent(
            new Event('blur', {
                bubbles: true
            })
        );
        """,
        field,
        value_iso,
    )

    valor_preenchido = field.get_attribute(
        "value"
    )

    if valor_preenchido != value_iso:
        raise ExportError(
            f"O campo {nome_campo} não foi preenchido corretamente. "
            f"Esperado: {value_iso!r}. "
            f"Encontrado: {valor_preenchido!r}. "
            f"Locator: {locator}."
        )

    logger.info(
        "produção | campo de data preenchido | "
        "campo=%s | valor=%s",
        nome_campo,
        value_iso,
    )


def _normalizar_texto(value: str) -> str:
    """Normaliza um texto para comparação."""

    return " ".join(
        value.strip().casefold().split()
    )


def _selecionar_pagamento_cliente(
    driver: Any,
    wait: WebDriverWait,
) -> None:
    """Seleciona Pagamento ao cliente pelo componente visual da página."""

    locator = (
        ProducaoSelectors.RELATORIO_TIPO_DATA
    )

    quantidade_encontrada = len(
        driver.find_elements(*locator)
    )

    logger.info(
        "produção | procurando filtro Tipo de Data | "
        "locator=%s | url=%s | titulo=%s | "
        "quantidade_encontrada=%d",
        locator,
        driver.current_url,
        driver.title,
        quantidade_encontrada,
    )

    # Não usar element_to_be_clickable.
    # O select original está oculto pelo bootstrap-select.
    field = wait.until(
        EC.presence_of_element_located(
            locator
        )
    )

    tag_name = field.tag_name.casefold()

    if tag_name != "select":
        raise ExportError(
            "RELATORIO_TIPO_DATA não aponta para um "
            f"elemento <select>. Elemento encontrado: <{tag_name}>. "
            f"Locator: {locator}."
        )

    select = Select(field)

    opcoes = [
        {
            "value": option.get_attribute("value") or "",
            "text": option.text.strip(),
        }
        for option in select.options
    ]

    logger.info(
        "produção | opções encontradas no Tipo de Data: %s",
        opcoes,
    )

    valor_pagamento: str | None = None

    # A opção confirmada no HTML usa value="2".
    for option in opcoes:
        if option["value"] == "2":
            valor_pagamento = "2"
            break

    # Fallback pelo texto, caso o value mude.
    if valor_pagamento is None:
        for option in opcoes:
            texto_normalizado = _normalizar_texto(
                option["text"]
            )

            if texto_normalizado in {
                "pagamento ao cliente",
                "pagamento cliente",
            }:
                valor_pagamento = option["value"]
                break

    if valor_pagamento is None:
        raise ExportError(
            "A opção 'Pagamento ao cliente' não foi encontrada "
            f"no filtro Tipo de Data. Opções disponíveis: {opcoes}."
        )

    logger.info(
        "produção | selecionando Pagamento ao cliente pelo bootstrap-select | value=%s",
        valor_pagamento,
    )

    # A interação com a opção exibida pelo bootstrap-select aciona o evento
    # que atualiza o modelo Vue. A alteração direta no <select> escondido era
    # anulada pela próxima renderização e mantinha o valor anterior ("1").
    clicar_elemento(
        driver,
        wait,
        ProducaoSelectors.RELATORIO_TIPO_DATA_BUTTON,
        "producao_abrir_tipo_data",
    )
    clicar_elemento(
        driver,
        wait,
        ProducaoSelectors.RELATORIO_PAGAMENTO_CLIENTE_OPTION,
        "producao_selecionar_pagamento_cliente",
    )

    def filtro_atualizado(current_driver: Any) -> tuple[str, str] | bool:
        current_field = current_driver.find_element(*locator)
        current_select = Select(current_field)
        valor = current_field.get_attribute("value")
        texto = current_select.first_selected_option.text.strip()

        if (
            valor == valor_pagamento
            and _normalizar_texto(texto)
            in {"pagamento ao cliente", "pagamento cliente"}
        ):
            return valor, texto

        return False

    valor_atual, texto_atual = wait.until(filtro_atualizado)
    texto_normalizado = _normalizar_texto(texto_atual)

    if valor_atual != valor_pagamento:
        raise ExportError(
            "O filtro Tipo de Data não foi atualizado. "
            f"Esperado: {valor_pagamento!r}. "
            f"Encontrado: {valor_atual!r}."
        )

    if texto_normalizado not in {
        "pagamento ao cliente",
        "pagamento cliente",
    }:
        raise ExportError(
            "O valor do filtro foi alterado, mas o texto "
            f"selecionado é {texto_atual!r}."
        )

    logger.info(
        "produção | filtro Tipo de Data selecionado | "
        "valor=%s | texto=%s",
        valor_atual,
        texto_atual,
    )


def exportar_producao(
    driver: Any = default_driver,
    data_inicial: str | None = None,
    data_final: str | None = None,
) -> Path:
    """Exporta o Excel Resumido do Relatório Geral."""

    default_initial, default_final = (
        get_periodo_producao()
    )

    initial = (
        data_inicial
        or default_initial
    )

    final = (
        data_final
        or default_final
    )

    report_wait = WebDriverWait(
        driver,
        WAIT_RELATORIO,
    )

    etapa = "inicializacao"

    logger.info(
        "produção | iniciando exportação do Relatório Geral"
    )

    logger.info(
        "produção | período consultado | "
        "inicial=%s | final=%s",
        initial,
        final,
    )

    try:
        etapa = "abrir_relatorio"

        logger.info(
            "produção | acessando Relatório Geral | url=%s",
            RELATORIO_PRODUCAO_URL,
        )

        driver.get(
            RELATORIO_PRODUCAO_URL
        )

        esperar_documento_carregar(
            driver,
            WAIT_RELATORIO,
        )

        logger.info(
            "produção | Relatório Geral carregado | "
            "url=%s | titulo=%s",
            driver.current_url,
            driver.title,
        )

        etapa = "abrir_painel_datas"

        _garantir_painel_datas(
            driver,
            report_wait,
        )

        etapa = "preencher_data_inicial"

        _preencher_data_relatorio(
            driver,
            report_wait,
            ProducaoSelectors.RELATORIO_DATA_INICIAL,
            initial,
            "data inicial",
        )

        etapa = "preencher_data_final"

        _preencher_data_relatorio(
            driver,
            report_wait,
            ProducaoSelectors.RELATORIO_DATA_FINAL,
            final,
            "data final",
        )

        etapa = "selecionar_tipo_data"

        _selecionar_pagamento_cliente(
            driver,
            report_wait,
        )

        etapa = "gerar_relatorio"

        logger.info(
            "produção | gerando relatório"
        )

        clicar_elemento(
            driver,
            report_wait,
            ProducaoSelectors.RELATORIO_GERAR,
            "producao_gerar_relatorio",
        )

        etapa = "aguardar_loading"

        esperar_loading_desaparecer(
            driver,
            ProducaoSelectors.RELATORIO_LOADING,
            WAIT_RELATORIO,
        )

        etapa = "aguardar_tabela"

        esperar_tabela_carregar(
            driver,
            ProducaoSelectors.RELATORIO_TABELA,
            WAIT_RELATORIO,
        )

        logger.info(
            "produção | tabela carregada"
        )

        etapa = "snapshot_downloads"

        files_before_export = (
            snapshot_downloads()
        )

        etapa = "abrir_exportacao"

        logger.info(
            "produção | abrindo opções de exportação"
        )

        clicar_elemento(
            driver,
            report_wait,
            ProducaoSelectors.RELATORIO_EXPORT_BUTTON,
            "producao_abrir_exportacao",
        )

        etapa = "selecionar_excel_resumido"

        logger.info(
            "produção | selecionando Excel Resumido"
        )

        clicar_elemento(
            driver,
            report_wait,
            ProducaoSelectors.RELATORIO_EXCEL_RESUMIDO,
            "producao_excel_resumido",
        )

        etapa = "confirmar_download"

        logger.info(
            "produção | confirmando download do arquivo gerado"
        )

        clicar_elemento(
            driver,
            report_wait,
            ProducaoSelectors.RELATORIO_BAIXAR_ARQUIVO,
            "producao_baixar_arquivo",
        )

        etapa = "aguardar_download"

        logger.info(
            "produção | aguardando conclusão do download"
        )

        downloaded_file = wait_download(
            files_before_export
        )

        downloaded_path = Path(
            downloaded_file
        )

        if not downloaded_path.is_file():
            raise DownloadError(
                "O download foi informado como concluído, "
                f"mas o arquivo não foi encontrado: {downloaded_path}"
            )

        if downloaded_path.stat().st_size == 0:
            raise DownloadError(
                f"O arquivo baixado está vazio: {downloaded_path}"
            )

        logger.info(
            "produção | download concluído | "
            "arquivo=%s | tamanho_bytes=%d",
            downloaded_path,
            downloaded_path.stat().st_size,
        )

        return downloaded_path

    except TimeoutException as error:
        logger.exception(
            "produção | timeout | etapa=%s | "
            "url=%s | titulo=%s",
            etapa,
            driver.current_url,
            driver.title,
        )

        evidence = registrar_evidencia_erro(
            driver,
            f"producao_timeout_{etapa}",
            erro=error,
        )

        raise ExportError(
            "Falha por timeout na exportação da produção. "
            f"Etapa: {etapa}. "
            f"URL: {driver.current_url}. "
            f"Tipo da causa: {type(error).__name__}. "
            f"Evidências: {evidence}"
        ) from error

    except DownloadError as error:
        logger.exception(
            "produção | erro de download | "
            "etapa=%s | erro=%s",
            etapa,
            error,
        )

        evidence = registrar_evidencia_erro(
            driver,
            f"producao_download_{etapa}",
            erro=error,
        )

        raise ExportError(
            "Falha ao baixar o relatório de produção. "
            f"Etapa: {etapa}. "
            f"Causa: {error}. "
            f"Evidências: {evidence}"
        ) from error

    except ExportError as error:
        logger.exception(
            "produção | erro de exportação | "
            "etapa=%s | erro=%s",
            etapa,
            error,
        )

        evidence = registrar_evidencia_erro(
            driver,
            f"producao_exportacao_{etapa}",
            erro=error,
        )

        raise ExportError(
            f"{error} "
            f"Etapa: {etapa}. "
            f"Evidências: {evidence}"
        ) from error

    except Exception as error:
        logger.exception(
            "produção | falha inesperada | "
            "etapa=%s | tipo=%s | erro=%s",
            etapa,
            type(error).__name__,
            error,
        )

        evidence = registrar_evidencia_erro(
            driver,
            f"producao_inesperado_{etapa}",
            erro=error,
        )

        raise ExportError(
            "Falha inesperada na exportação da produção. "
            f"Etapa: {etapa}. "
            f"Causa: {type(error).__name__}: {error}. "
            f"Evidências: {evidence}"
        ) from error

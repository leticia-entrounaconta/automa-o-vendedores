"""Seletores Selenium centralizados e confirmados na interface 2Tech."""

from __future__ import annotations

from typing import TypeAlias

from selenium.webdriver.common.by import By

Locator: TypeAlias = tuple[str, str]


class VendedoresSelectors:
    """Seletores utilizados na exportação dos vendedores ativos."""

    FILTERS_BUTTON: Locator = (By.ID, "btnExibeFiltro")
    CADASTRO_TAB: Locator = (
        By.XPATH,
        "//a[@role='tab'][.//h6[normalize-space()='Cadastro']]",
    )
    SITUACAO_DROPDOWN: Locator = (By.CSS_SELECTOR, "button[data-id='ddlSituacaoVendedor']")
    ATIVO_OPTION: Locator = (By.XPATH, "//span[normalize-space()='Ativo']")
    SEARCH_BUTTON: Locator = (By.XPATH, "//button[contains(normalize-space(.), 'Pesquisar')]")
    EXPORT_BUTTON: Locator = (By.XPATH, "//button[contains(normalize-space(.), 'Exportar')]")


class ProducaoSelectors:
    """Seletores utilizados no Relatório Geral da 2Tech."""

    RELATORIO_DATAS_TAB: Locator = (
        By.XPATH,
        "//a[@role='tab'][.//h6[normalize-space()='Datas']]",
    )
    RELATORIO_DATA_INICIAL: Locator = (
        By.ID,
        "txtDataInicial",
    )

    RELATORIO_DATA_FINAL: Locator = (
        By.ID,
        "txtDataFinal",
    )
    # Select nativo; a interface Bootstrap cria apenas a apresentação visual.
    RELATORIO_TIPO_DATA: Locator = (
        By.ID,
        "ddlTipoData",
    )
    # O <select> é controlado pelo Vue e estilizado pelo bootstrap-select.
    # A seleção deve ocorrer pela opção visual para disparar a atualização do
    # modelo da página; alterar somente o <select> oculto é revertido pelo Vue.
    RELATORIO_TIPO_DATA_BUTTON: Locator = (
        By.CSS_SELECTOR,
        "button[data-id='ddlTipoData']",
    )
    RELATORIO_PAGAMENTO_CLIENTE_OPTION: Locator = (
        By.XPATH,
        "//button[@data-id='ddlTipoData']"
        "/following-sibling::div[contains(@class, 'dropdown-menu')]"
        "//a[.//span[normalize-space()='Pagamento ao cliente']]",
    )
    RELATORIO_GERAR: Locator = (
        By.XPATH,
        "//button[normalize-space()='Gerar relatório']",
    )
    RELATORIO_TABELA: Locator = (
        By.ID,
        "tableResultado",
    )
    RELATORIO_EXPORT_BUTTON: Locator = (
        By.XPATH,
        "//button[@data-toggle='dropdown' and contains(normalize-space(.), 'Exportar')]",
    )
    RELATORIO_EXCEL_RESUMIDO: Locator = (
        By.XPATH,
        "//ul[contains(@class, 'dropdown-menu')]//a[normalize-space()='Excel Resumido']",
    )
    # Modal SweetAlert exibido após o relatório ser preparado pela 2Tech.
    RELATORIO_BAIXAR_ARQUIVO: Locator = (
        By.XPATH,
        "//button[normalize-space()='Baixar arquivo']",
    )
    # Não há um overlay estável confirmado no Relatório Geral; a tabela é o
    # sinal de conclusão da consulta.
    RELATORIO_LOADING: tuple[Locator, ...] = ()

    # Aliases para compatibilidade com outros módulos.
    DATA_INICIAL: Locator = RELATORIO_DATA_INICIAL
    DATA_FINAL: Locator = RELATORIO_DATA_FINAL


class ImportacaoProducaoSelectors:
    """Seletores isolados da tela Operacional > Produção - Layout.

    Esta tela recebe arquivos e não participa da coleta do Relatório Geral.
    """

    DATA_INICIAL: Locator = (By.ID, "txtDataInicial")
    DATA_FINAL: Locator = (By.ID, "txtDataFinal")
    APPLY_FILTERS: Locator = (
        By.XPATH,
        "//button[contains(@onclick, 'CarregaDadosImportacao') "
        "and contains(normalize-space(.), 'Aplicar Filtro')]",
    )
    IMPORT_FILE_BUTTON: Locator = (
        By.XPATH,
        "//*[self::a or self::button][contains(normalize-space(.), 'Importar Arquivo')]",
    )
    IMPORT_FILE_MODAL: Locator = (By.ID, "modalImportacaoPorArquivo")
    IMPORT_FILE_IFRAME: Locator = (By.ID, "iframeImportacaoPorArquivo")
    IMPORT_FILE_INPUT: Locator = (By.ID, "input-file")
    IMPORT_CORRESPONDENTE: Locator = (By.ID, "ddlCorrespondente")
    IMPORT_LAYOUT: Locator = (By.ID, "Layout_Importacao_Digitacao_Proposta_Id")
    IMPORT_BANCO: Locator = (By.ID, "Banco_Id")
    IMPORT_DATA_INICIAL: Locator = (By.ID, "txtDataInicial")
    IMPORT_DATA_FINAL: Locator = (By.ID, "txtDataFinal")
    IMPORT_TIPO_DATA: Locator = (By.ID, "ddlTipoDeData")
    IMPORT_SUBMIT_BUTTON: Locator = (By.ID, "btnEnviar")

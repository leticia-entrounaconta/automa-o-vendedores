import logging
import os
from pathlib import Path
from time import gmtime, strftime, time

from app.actions.auth import make_login_2tech
from app.browser.exceptions import AutomationError
from app.actions.navigation import (
    navigate_to_cadastros,
    navigate_to_system,
    navigate_to_vendedores,
)
from app.actions.producao import exportar_producao
from app.actions.vendedores import exportar_vendedores_ativos
from app.data_processing.cruzamento_handler import (
    cruzar_vendedores_producao,
)
from app.data_processing.producao_handler import tratar_producao
from app.data_processing.vendedores_handler import tratar_vendedores
from app.integrations.sharepoint import (
    enviar_arquivo_sharepoint,
    sharepoint_habilitado,
)
from app.settings.config import get_periodo_producao
from app.settings.driver_settings import driver
from app.settings.logging_config import configure_logging
from app.validations.files import (
    validar_arquivo_producao,
    validar_arquivo_vendedores,
)


configure_logging()

for noisy_logger in (
    "selenium",
    "urllib3",
    "requests",
):
    logging.getLogger(noisy_logger).setLevel(logging.WARNING)

logger = logging.getLogger("rpa_main")


def obter_booleano_env(
    nome: str,
    padrao: bool = False,
) -> bool:
    """Converte uma variável de ambiente para booleano."""

    valor_padrao = "true" if padrao else "false"

    valor = os.getenv(
        nome,
        valor_padrao,
    ).strip().lower()

    return valor in {
        "1",
        "true",
        "sim",
        "yes",
        "on",
    }


def enviar_arquivos_gerados_ao_sharepoint(*arquivos: Path) -> None:
    """Envia os relatórios finais após a geração local bem-sucedida."""
    logger.info("Iniciando envio de %d arquivos ao SharePoint", len(arquivos))
    for arquivo in arquivos:
        enviar_arquivo_sharepoint(arquivo, arquivo.name)
        logger.info("Arquivo enviado ao SharePoint: %s", arquivo.name)


def executar_automacao() -> None:
    """Executa o fluxo de vendedores e produção na mesma sessão da 2Tech."""

    start_time = time()
    etapa = "inicialização"
    vendedores_count = 0
    producao_count = 0
    vendedores = None
    producao = None
    resultado = None
    status = "falha"

    logger.info(
        "Início da automação de vendedores e produção"
    )

    try:
        etapa = "login"
        navigate_to_system()
        make_login_2tech()

        etapa = "exportação de vendedores"
        logger.info(
            "Iniciando coleta de vendedores ativos"
        )

        navigate_to_cadastros()
        navigate_to_vendedores()

        vendedores_bruto = exportar_vendedores_ativos()

        vendedores = tratar_vendedores(
            vendedores_bruto
        )

        vendedores_count = validar_arquivo_vendedores(
            vendedores
        )

        logger.info(
            "Vendedores ativos: %d | arquivo: %s",
            vendedores_count,
            vendedores,
        )

        # Produção pode ficar desabilitada até o relatório correto ser configurado.
        producao_habilitada = obter_booleano_env(
            "PRODUCAO_ENABLED",
            padrao=False,
        )

        if not producao_habilitada:
            logger.warning(
                "Rotina de produção desabilitada. "
                "Somente o relatório de vendedores foi processado."
            )
            status = "sucesso parcial"
            return

        etapa = "exportação da produção"
        logger.info(
            "Iniciando coleta do relatório de produção"
        )

        data_inicial, data_final = get_periodo_producao()

        logger.info(
            "Período da produção: %s até %s",
            data_inicial,
            data_final,
        )

        producao_bruta = exportar_producao(
            data_inicial=data_inicial,
            data_final=data_final,
        )

        producao = tratar_producao(
            producao_bruta
        )

        producao_count = validar_arquivo_producao(
            producao
        )

        logger.info(
            "Registros de produção: %d | arquivo: %s",
            producao_count,
            producao,
        )

        etapa = "cruzamento"
        logger.info(
            "Iniciando cruzamento entre vendedores e produção"
        )

        resultado = cruzar_vendedores_producao(
            vendedores,
            producao,
        )

        logger.info(
            "Arquivo final de parceiros classificados: %s",
            resultado,
        )

        if sharepoint_habilitado():
            etapa = "envio ao SharePoint"
            enviar_arquivos_gerados_ao_sharepoint(vendedores, producao, resultado)
        else:
            logger.info("Integração com SharePoint desabilitada.")

        logger.info(
            "Automação concluída com sucesso"
        )
        status = "sucesso"

    except AutomationError:
        logger.exception("Falha de automação | etapa=%s", etapa)
        raise
    except Exception:
        logger.exception(
            "Falha inesperada | etapa=%s",
            etapa,
        )
        raise

    finally:
        duration = strftime(
            "%H:%M:%S",
            gmtime(time() - start_time),
        )

        logger.info(
            "Execução finalizada em %s",
            duration,
        )
        logger.info(
            "Resumo final | status=%s | vendedores=%d | produções=%d | "
            "arquivo_vendedores=%s | arquivo_producao=%s | resultado=%s | tempo=%s",
            status,
            vendedores_count,
            producao_count,
            vendedores,
            producao,
            resultado,
            duration,
        )

        if driver is not None:
            try:
                driver.quit()

                logger.info(
                    "Driver finalizado."
                )

            except Exception:
                logger.exception(
                    "Erro ao finalizar o driver."
                )


def main() -> None:
    """Ponto de entrada da aplicação."""

    executar_automacao()


if __name__ == "__main__":
    main()

"""RPA Template — Main entry point.

This module demonstrates the standard RPA execution pattern:
1. Configure logging
2. Initialize WebDriver
3. Execute automation steps
4. Handle errors
5. Clean up WebDriver resources

Customize the main() function with your automation logic.
"""

"""RPA Template — Main entry point."""

import logging
from time import time, strftime, gmtime

from app.settings.driver_settings import driver
from app.settings.logging_config import configure_logging
from app.utils.colors import TextColor, reset

# Login
from app.actions.auth import make_login_2tech

# Navegação
from app.actions.navigation import (
    navigate_to_system,
    navigate_to_cadastros,
    navigate_to_vendedores,
)

# Interações da tela de vendedores
from app.actions.element_interaction import export_vendedores_ativos

# Tratamento do Excel
from app.data_processing.excel_handler import clean_excel


configure_logging()

for noisy_logger in ("selenium", "urllib3", "requests"):
    logging.getLogger(noisy_logger).setLevel(logging.WARNING)

logger = logging.getLogger("rpa_main")


def main():
    start_time = time()
    logger.info(f"{TextColor.green}Inicio da execucao do RPA...{reset}")

    try:
        # Sistema
        logger.info("Acessando sistema 2Tech")
        navigate_to_system()

        # Login
        logger.info("Realizando login na 2Tech")
        make_login_2tech()

        # Navegação
        logger.info("Navegando para Cadastros")
        navigate_to_cadastros()

        logger.info("Navegando para Vendedores")
        navigate_to_vendedores()

        # Exportação
        logger.info("Filtrando vendedores ativos e exportando relatório")
        file_path = export_vendedores_ativos()

        if file_path is None:
            logger.warning("Nenhum arquivo foi exportado.")
            return

        # Limpeza da planilha
        logger.info("Limpando planilha exportada")
        clean_file = clean_excel(file_path)

        if clean_file is None:
            logger.warning("Falha ao limpar planilha.")
            return

        logger.info("Planilha final gerada em: %s", clean_file)

    except Exception as error:
        logger.exception("Erro durante execucao: %s", error)
        raise

    finally:
        duration = strftime("%H:%M:%S", gmtime(time() - start_time))
        logger.info(f"{TextColor.green}Execucao finalizada em {duration}{reset}")

        driver.quit()
        logger.info("Driver finalizado.")


if __name__ == "__main__":
    main()
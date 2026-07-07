"""RPA Template — Main entry point.

This module demonstrates the standard RPA execution pattern:
  1. Configure logging
  2. Initialize WebDriver
  3. Execute automation steps
  4. Handle errors
  5. Clean up WebDriver resources

Customize the `main()` function with your automation logic.
"""

import os
import logging
from app.settings.driver_settings import driver, wait
from app.settings.logging_config import configure_logging
from app.settings.secrets import webhook_url
from app.settings.config import DOWNLOAD_PATH
from app.utils.colors import TextColor, reset
from time import sleep, time, strftime, gmtime
from app.actions.auth import make_login
from app.actions.navigation import navigate_to_relatorio
from app.actions.element_interaction import baixar_relatorio
from app.data_processing.excel_handler import clean_excel

configure_logging()

for noisy_logger in ("selenium", "urllib3", "requests"):
    logging.getLogger(noisy_logger).setLevel(logging.WARNING)

logger = logging.getLogger("rpa_main")

def main():
    start_time = time()
    logger.info(f"{TextColor.green}Inicio da execucao do RPA...{reset}")

    try:
        # ── Step 1: Login ────────────────────────────────────────────
        
        logger.info("Acessando sistema Red Consig")

        # ── Step 2: Navigation ───────────────────────────────────────
        
        logger.info("Navegando para o Relatorio")

        # ── Step 3: Data extraction / processing ─────────────────────
        
        logger.info("Baixar Relatorio")
        
    except Exception as error:
        logger.exception("Erro durante execucao: %s", error)
        raise
    finally:
        logger.info(f"{TextColor.green}Execucao finalizada em {strftime('%H:%M:%S', gmtime(time() - start_time))}{reset}")
        driver.quit()
        logger.info("Driver finalizado.")


if __name__ == "__main__":
    main()

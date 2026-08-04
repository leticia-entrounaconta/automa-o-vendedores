"""Evidence capture for Selenium failures."""

from __future__ import annotations

from datetime import datetime
import logging
from pathlib import Path
from typing import Any

from app.settings.config import ERROR_EVIDENCE_DIR

logger = logging.getLogger(__name__)


def _safe_name(value: str) -> str:
    return "".join(character if character.isalnum() else "_" for character in value).strip("_")


def registrar_evidencia_erro(
    driver: Any,
    etapa: str,
    locator: tuple[str, str] | None = None,
    erro: BaseException | None = None,
) -> Path:
    """Save screenshot, HTML and diagnostics without hiding the original error."""
    ERROR_EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    prefix = f"{datetime.now():%Y-%m-%d_%H%M%S}_{_safe_name(etapa)}"
    base_path = ERROR_EVIDENCE_DIR / prefix
    screenshot_path = base_path.with_suffix(".png")
    html_path = base_path.with_suffix(".html")
    details_path = base_path.with_suffix(".txt")

    try:
        driver.save_screenshot(str(screenshot_path))
        html_path.write_text(driver.page_source, encoding="utf-8")
        details_path.write_text(
            "\n".join(
                (
                    f"etapa={etapa}",
                    f"url={driver.current_url}",
                    f"titulo={driver.title}",
                    f"locator={locator}",
                    f"excecao={type(erro).__name__ if erro else ''}",
                    f"mensagem={erro or ''}",
                )
            ),
            encoding="utf-8",
        )
        logger.error("Evidências salvas em %s", base_path)
    except Exception:
        logger.exception("Não foi possível salvar evidências da etapa %s", etapa)
    return base_path

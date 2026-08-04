"""Exportação atômica das bases analíticas."""

from __future__ import annotations

import logging
from pathlib import Path
from time import sleep
from uuid import uuid4

import pandas as pd

from app.data_processing.validators import garantir_dataframe_nao_vazio

logger = logging.getLogger(__name__)


class ArquivoSaidaBloqueadoError(PermissionError):
    """Arquivo final aberto por outro processo, normalmente o Excel."""


def _substituir_arquivo_temporario(
    temporario: Path,
    caminho_saida: Path,
    tentativas: int = 3,
) -> None:
    """Tenta a troca atômica sem apagar a versão anterior em caso de bloqueio."""
    for tentativa in range(1, tentativas + 1):
        try:
            temporario.replace(caminho_saida)
            return
        except PermissionError as error:
            if tentativa == tentativas:
                raise ArquivoSaidaBloqueadoError(
                    f"Não foi possível atualizar '{caminho_saida.name}' porque ele está aberto "
                    "em outro programa. Feche o arquivo no Excel e execute novamente."
                ) from error
            logger.warning(
                "Arquivo de saída bloqueado | arquivo=%s | tentativa=%d/%d",
                caminho_saida.name,
                tentativa,
                tentativas,
            )
            sleep(1)


def exportar_excel_atomico(
    dataframe: pd.DataFrame,
    caminho_saida: Path,
    contexto: str,
    controle: dict[str, object] | None = None,
    producoes_nao_relacionadas: pd.DataFrame | None = None,
) -> Path:
    """Grava e valida um temporário antes de substituir o artefato final.

    A primeira aba é sempre ``DADOS``; quando presente, ``CONTROLE`` registra
    a rastreabilidade da execução sem interferir nas leituras existentes.
    """
    garantir_dataframe_nao_vazio(dataframe, contexto)
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho_saida.with_name(
        f".{caminho_saida.stem}.{uuid4().hex}.tmp{caminho_saida.suffix}"
    )
    try:
        with pd.ExcelWriter(temporario) as writer:
            dataframe.to_excel(writer, sheet_name="DADOS", index=False)
            if controle:
                pd.DataFrame([controle]).to_excel(writer, sheet_name="CONTROLE", index=False)
            if producoes_nao_relacionadas is not None and not producoes_nao_relacionadas.empty:
                producoes_nao_relacionadas.to_excel(
                    writer, sheet_name="PRODUCOES_NAO_RELACIONADAS", index=False
                )
        if not temporario.is_file() or temporario.stat().st_size == 0:
            raise ValueError(f"{contexto}: a exportação temporária ficou vazia.")
        validar = pd.read_excel(temporario, sheet_name="DADOS")
        garantir_dataframe_nao_vazio(validar, contexto)
        _substituir_arquivo_temporario(temporario, caminho_saida)
    finally:
        if temporario.exists():
            try:
                temporario.unlink()
            except PermissionError:
                logger.warning("Arquivo temporário não pôde ser removido: %s", temporario)
    logger.info("%s salvo em %s", contexto, caminho_saida)
    return caminho_saida

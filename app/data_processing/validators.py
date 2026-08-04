"""Validações reutilizáveis para as bases analíticas da automação."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


class DataProcessingValidationError(ValueError):
    """Dados ausentes ou inconsistentes para a etapa de processamento."""


def garantir_dataframe_nao_vazio(dataframe: pd.DataFrame, contexto: str) -> None:
    if dataframe.empty:
        raise DataProcessingValidationError(f"{contexto}: nenhum registro válido foi encontrado.")


def validar_colunas_obrigatorias(
    dataframe: pd.DataFrame, colunas: set[str], contexto: str
) -> None:
    ausentes = sorted(colunas.difference(dataframe.columns))
    if ausentes:
        raise DataProcessingValidationError(
            f"{contexto}: colunas obrigatórias ausentes: {ausentes}. "
            f"Colunas encontradas: {list(dataframe.columns)}"
        )


def validar_arquivo_existente(caminho: Path, contexto: str) -> None:
    if not caminho.is_file():
        raise FileNotFoundError(f"{contexto}: arquivo não encontrado em {caminho}")
    if caminho.stat().st_size == 0:
        raise DataProcessingValidationError(f"{contexto}: arquivo está vazio em {caminho}")


def validar_percentual_maximo(
    serie: pd.Series, percentual_maximo: float, descricao: str, contexto: str
) -> None:
    if serie.empty:
        return
    percentual = float(serie.isna().mean() * 100)
    if percentual > percentual_maximo:
        raise DataProcessingValidationError(
            f"{contexto}: {percentual:.1f}% de {descricao} inválidos; "
            f"limite permitido: {percentual_maximo:.1f}%."
        )

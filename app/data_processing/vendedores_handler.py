"""Tratamento determinístico da base cadastral de vendedores."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from app.data_processing.column_mappings import VENDEDORES_COLUMN_MAPPING, standardize_columns
from app.data_processing.excel_handler import VENDEDORES_REMOVER
from app.data_processing.export_handler import exportar_excel_atomico
from app.data_processing.normalization import (
    limpar_texto,
    normalizar_codigo_vendedor,
    normalizar_data,
    normalizar_documento,
    normalizar_status,
)
from app.data_processing.validators import (
    garantir_dataframe_nao_vazio,
    validar_colunas_obrigatorias,
)
from app.settings.config import VENDEDORES_OUTPUT_PATH

logger = logging.getLogger(__name__)

COLUNAS_OBRIGATORIAS_VENDEDORES = {
    "codigo_vendedor",
    "nome_vendedor",
    "situacao_cadastral",
}
CAMPOS_VENDEDORES = [
    "codigo_vendedor",
    "cpf_cnpj",
    "nome_vendedor",
    "situacao_cadastral",
    "grupo_vendedor",
    "responsavel_comercial",
    "data_cadastro",
]


def tratar_dataframe_vendedores(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Padroniza, filtra e deduplica vendedores sem efeitos de arquivo."""
    original = len(dataframe)
    result = dataframe.replace(r"^\s*$", pd.NA, regex=True).dropna(how="all").copy()
    garantir_dataframe_nao_vazio(result, "Relatório bruto de vendedores")
    result = standardize_columns(result, VENDEDORES_COLUMN_MAPPING)
    validar_colunas_obrigatorias(result, COLUNAS_OBRIGATORIAS_VENDEDORES, "Relatório de vendedores")

    for coluna in CAMPOS_VENDEDORES:
        if coluna not in result.columns:
            result[coluna] = pd.NA
    result = result.loc[:, CAMPOS_VENDEDORES].copy()
    result["codigo_vendedor"] = result["codigo_vendedor"].map(normalizar_codigo_vendedor)
    result["cpf_cnpj"] = result["cpf_cnpj"].map(normalizar_documento)
    for coluna in ("nome_vendedor", "situacao_cadastral", "grupo_vendedor", "responsavel_comercial"):
        result[coluna] = result[coluna].map(limpar_texto).replace("", pd.NA)
    result["data_cadastro"] = normalizar_data(result["data_cadastro"])

    grupos_excluidos = {normalizar_status(grupo) for grupo in VENDEDORES_REMOVER}
    grupos = result["grupo_vendedor"].map(normalizar_status)
    result = result.loc[~grupos.isin(grupos_excluidos)].copy()
    situacoes = result["situacao_cadastral"].map(normalizar_status)
    result = result.loc[situacoes.eq("ATIVO")].copy()
    sem_codigo = int(result["codigo_vendedor"].eq("").sum())
    if sem_codigo:
        logger.warning("Vendedores removidos sem código: %d", sem_codigo)
        result = result.loc[result["codigo_vendedor"].ne("")].copy()

    # Na ausência de uma regra de atualização confiável, preserva o registro
    # cadastral mais completo e, em empate, a primeira ocorrência do arquivo.
    result["_completude"] = result.notna().sum(axis=1)
    result["_ordem_origem"] = range(len(result))
    duplicados = int(result.duplicated("codigo_vendedor", keep=False).sum())
    result = (
        result.sort_values(
            ["codigo_vendedor", "_completude", "data_cadastro", "_ordem_origem"],
            ascending=[True, False, False, True],
            na_position="last",
        )
        .drop_duplicates("codigo_vendedor", keep="first")
        .drop(columns=["_completude", "_ordem_origem"])
        .reset_index(drop=True)
    )
    garantir_dataframe_nao_vazio(result, "Relatório tratado de vendedores")
    logger.info(
        "Vendedores tratados | entrada=%d | removidos=%d | duplicidades=%d | válidos=%d",
        original,
        original - len(result),
        duplicados,
        len(result),
    )
    return result


def tratar_vendedores(
    caminho_entrada: Path, caminho_saida: Path = VENDEDORES_OUTPUT_PATH
) -> Path:
    """Lê o relatório bruto e grava a entrada cadastral validada da análise."""
    return exportar_excel_atomico(
        tratar_dataframe_vendedores(pd.read_excel(caminho_entrada, dtype=str)),
        caminho_saida,
        "Relatório de vendedores",
    )

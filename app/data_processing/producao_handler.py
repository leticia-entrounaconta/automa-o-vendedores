"""Tratamento auditável da produção exportada pela 2Tech/Gerencial Crédito."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from app.data_processing.column_mappings import PRODUCAO_COLUMN_MAPPING, standardize_columns
from app.data_processing.export_handler import exportar_excel_atomico
from app.data_processing.normalization import (
    limpar_texto,
    normalizar_codigo_vendedor,
    normalizar_data,
    normalizar_documento,
    normalizar_status,
    normalizar_valor_monetario,
)
from app.data_processing.validators import (
    garantir_dataframe_nao_vazio,
    validar_colunas_obrigatorias,
)
from app.settings.config import (
    PRIORIDADE_DATA_PRODUCAO,
    PRODUCAO_OUTPUT_PATH,
    STATUS_PRODUCAO_VALIDA,
)

logger = logging.getLogger(__name__)

COLUNAS_OBRIGATORIAS_PRODUCAO = {
    "codigo_vendedor",
    "numero_proposta",
    "valor_producao",
}
CAMPOS_PRODUCAO = [
    "codigo_vendedor", "cpf_cnpj", "nome_vendedor", "numero_proposta",
    "data_pagamento", "data_producao", "data_digitacao", "data_atualizacao_proposta",
    "data_referencia_producao", "origem_data_referencia", "valor_producao", "banco",
    "produto", "situacao_proposta", "situacao_proposta_normalizada",
    "producao_validada_por_status", "tipo_data_disponivel", "possui_data_pagamento",
]


def _definir_data_referencia(result: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Aplica a prioridade configurada sem confundir digitação com pagamento."""
    colunas_data = {
        "pagamento": "data_pagamento",
        "producao": "data_producao",
        "digitacao": "data_digitacao",
    }
    for coluna in (*colunas_data.values(), "data_atualizacao_proposta"):
        if coluna not in result:
            result[coluna] = pd.NaT
        result[coluna] = normalizar_data(result[coluna])
    result["data_referencia_producao"] = pd.NaT
    result["origem_data_referencia"] = pd.Series("sem_data", index=result.index, dtype="string")
    for origem in reversed(PRIORIDADE_DATA_PRODUCAO):
        coluna = colunas_data[origem]
        mascara = result[coluna].notna()
        result.loc[mascara, "data_referencia_producao"] = result.loc[mascara, coluna]
        result.loc[mascara, "origem_data_referencia"] = origem
    result["tipo_data_disponivel"] = result["origem_data_referencia"].replace({"sem_data": pd.NA})
    result["possui_data_pagamento"] = result["data_pagamento"].notna()
    invalidas = int(result["data_referencia_producao"].isna().sum())
    return result, invalidas


def _deduplicar_propostas(result: pd.DataFrame) -> pd.DataFrame:
    """Mantém a atualização mais recente; empates usam a ordem original estável."""
    result["numero_proposta"] = result["numero_proposta"].map(normalizar_codigo_vendedor)
    sem_proposta = result["numero_proposta"].eq("")
    if sem_proposta.any():
        logger.warning("Produções removidas sem número de proposta: %d", int(sem_proposta.sum()))
        result = result.loc[~sem_proposta].copy()
    result["_ordem_origem"] = range(len(result))
    antes = len(result)
    result = (
        result.sort_values(
            ["data_atualizacao_proposta", "data_referencia_producao", "_ordem_origem"],
            ascending=[False, False, True],
            na_position="last",
        )
        .drop_duplicates("numero_proposta", keep="first")
        .drop(columns="_ordem_origem")
        .reset_index(drop=True)
    )
    removidas = antes - len(result)
    if removidas:
        logger.info(
            "Duplicidades de proposta removidas: %d | critério=data_atualizacao,data_referencia,ordem_origem",
            removidas,
        )
    return result


def _normalizar_campos_texto(result: pd.DataFrame) -> pd.DataFrame:
    for coluna in ("nome_vendedor", "banco", "produto", "situacao_proposta"):
        result[coluna] = result[coluna].map(limpar_texto).replace("", pd.NA)
    result["situacao_proposta_normalizada"] = result["situacao_proposta"].map(normalizar_status)
    return result


def tratar_dataframe_producao(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Entrega uma base canônica, rastreável e sem propostas repetidas."""
    original = len(dataframe)
    result = dataframe.replace(r"^\s*$", pd.NA, regex=True).dropna(how="all").copy()
    garantir_dataframe_nao_vazio(result, "Relatório bruto de produção")
    result = standardize_columns(result, PRODUCAO_COLUMN_MAPPING)
    validar_colunas_obrigatorias(result, COLUNAS_OBRIGATORIAS_PRODUCAO, "Relatório de produção")
    for coluna in PRODUCAO_COLUMN_MAPPING:
        if coluna not in result:
            result[coluna] = pd.NA

    result["codigo_vendedor"] = result["codigo_vendedor"].map(normalizar_codigo_vendedor)
    result["cpf_cnpj"] = result["cpf_cnpj"].map(normalizar_documento)
    result["valor_producao"] = normalizar_valor_monetario(result["valor_producao"])
    result = _normalizar_campos_texto(result)
    result, datas_invalidas = _definir_data_referencia(result)
    sem_data = result["data_referencia_producao"].isna()
    if sem_data.any():
        logger.warning("Produções removidas sem data analítica: %d", int(sem_data.sum()))
        result = result.loc[~sem_data].copy()
    result = _deduplicar_propostas(result)

    if STATUS_PRODUCAO_VALIDA:
        status_validos = {normalizar_status(status) for status in STATUS_PRODUCAO_VALIDA}
        result["producao_validada_por_status"] = result["situacao_proposta_normalizada"].isin(status_validos)
    else:
        result["producao_validada_por_status"] = pd.Series(pd.NA, index=result.index, dtype="boolean")
        logger.warning("STATUS_PRODUCAO_VALIDA não configurado; não há confirmação de venda por status.")

    sem_codigo = int(result["codigo_vendedor"].eq("").sum())
    if sem_codigo:
        logger.warning("Produções sem código do vendedor: %d", sem_codigo)
    garantir_dataframe_nao_vazio(result, "Relatório tratado de produção")
    logger.info(
        "Produção tratada | entrada=%d | processadas=%d | sem_data=%d | sem_codigo=%d",
        original, len(result), datas_invalidas, sem_codigo,
    )
    return result.loc[:, CAMPOS_PRODUCAO]


def tratar_producao(caminho_entrada: Path, caminho_saida: Path = PRODUCAO_OUTPUT_PATH) -> Path:
    """Lê a exportação bruta e grava a produção validada para consolidação."""
    return exportar_excel_atomico(
        tratar_dataframe_producao(pd.read_excel(caminho_entrada, dtype=str)),
        caminho_saida,
        "Relatório de produção",
    )

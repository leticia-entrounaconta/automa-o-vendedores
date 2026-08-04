"""Central mapping between 2Tech spreadsheet headings and canonical headings."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import re
import unicodedata

import pandas as pd


class ColumnMappingError(ValueError):
    """Raised when a report has ambiguous headings for one canonical field."""


VENDEDORES_COLUMN_MAPPING: Mapping[str, Sequence[str]] = {
    "codigo_vendedor": ("Código Vendedor", "Codigo Vendedor", "CodVendedor"),
    "cpf_cnpj": ("CPF/CNPJ", "CPF CNPJ", "Documento", "CPF", "CNPJ"),
    "nome_vendedor": ("Nome Vendedor", "Vendedor", "Nome do Vendedor"),
    "situacao_cadastral": ("Situação Cadastral", "Situacao Cadastral", "Situação Vendedor", "SituacaoVendedor"),
    "grupo_vendedor": ("GrupoVendedor", "Grupo Vendedor", "Grupo"),
    "responsavel_comercial": (
        "Responsável Comercial",
        "Responsavel Comercial",
        "Comercial Responsável",
        "Gerente Comercial",
    ),
    "data_cadastro": ("Data Cadastro", "Data de Cadastro", "Dt Cadastro", "Cadastro"),
}

PRODUCAO_COLUMN_MAPPING: Mapping[str, Sequence[str]] = {
    "codigo_vendedor": (
        "Código Vendedor",
        "Codigo Vendedor",
        "CodVendedor",
        "Código Parceiro",
        "Código Corretor",
        "Codigo Corretor",
    ),
    "cpf_cnpj": ("CPF/CNPJ", "CPF CNPJ", "Documento", "CPF", "CNPJ"),
    "nome_vendedor": ("Nome Vendedor", "Vendedor", "Nome do Vendedor", "Parceiro", "Corretor"),
    "numero_proposta": (
        "Nº Proposta",
        "Nº Proposta/ADE",
        "No Proposta",
        "Número Proposta",
        "Numero Proposta",
        "Proposta",
    ),
    "data_producao": ("Data Produção", "Data Producao", "Data da Produção"),
    "data_pagamento": (
        "Data de Pagamento",
        "Data Pagamento",
        "Data do Pagamento",
        "Data Pagto",
    ),
    # Excel Resumido não expõe a data de pagamento. A data de digitação é
    # preservada separadamente e usada como referência somente quando não há
    # uma data de produção explícita no arquivo.
    "data_digitacao": ("Data de Digitação", "Data de Digitacao"),
    "data_atualizacao_proposta": (
        "Data Atualização",
        "Data Atualizacao",
        "Data Status Esteira",
        "DataStatusEsteira",
    ),
    "valor_producao": (
        "Valor Produção",
        "Valor Producao",
        "Valor Bruto",
        "Valor Liberado",
    ),
    "banco": ("Banco", "Banco/Correspondente", "Banco / Correspondente"),
    "produto": ("Produto", "Produto/Convênio", "Produto Convenio"),
    "situacao_proposta": (
        "Situação Proposta",
        "Situacao Proposta",
        "Status Proposta",
        "StatusEsteira",
    ),
}


def normalize_column_name(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def standardize_columns(
    dataframe: pd.DataFrame, mapping: Mapping[str, Sequence[str]]
) -> pd.DataFrame:
    """Trim headers and rename the recognized 2Tech headings to canonical names."""
    result = dataframe.copy()
    result.columns = [str(column).strip() for column in result.columns]
    rename_map: dict[str, str] = {}

    for canonical, aliases in mapping.items():
        candidates = (canonical, *aliases)
        candidate_keys = {normalize_column_name(candidate) for candidate in candidates}
        sources = [column for column in result.columns if normalize_column_name(column) in candidate_keys]
        if len(sources) > 1:
            raise ColumnMappingError(
                f"Mapeamento ambíguo para '{canonical}': {sources}. "
                "Mantenha apenas um cabeçalho equivalente no relatório."
            )
        if sources and sources[0] != canonical:
            rename_map[sources[0]] = canonical

    return result.rename(columns=rename_map)

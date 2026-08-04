"""Normalization functions used by the production matching rules."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

import pandas as pd


def _is_empty(value: Any) -> bool:
    return value is None or pd.isna(value) or str(value).strip().lower() in {"", "nan", "none", "<na>"}


def normalize_code(value: Any) -> str:
    """Normalize seller codes while preserving meaningful letters and leading zeros."""
    if _is_empty(value):
        return ""
    text = str(value).strip()
    if re.fullmatch(r"\d+\.0", text):
        text = text[:-2]
    return re.sub(r"[^A-Za-z0-9]", "", text).upper()


def normalize_cpf_cnpj(value: Any) -> str:
    """Return only the document digits; callers must read documents as text."""
    if _is_empty(value):
        return ""
    text = str(value).strip()
    if re.fullmatch(r"\d+\.0", text):
        text = text[:-2]
    return re.sub(r"\D", "", text)


def normalize_name(value: Any) -> str:
    """Case-, accent-, whitespace- and punctuation-insensitive name key."""
    if _is_empty(value):
        return ""
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"[^A-Za-z0-9]+", " ", text).strip().upper()
    return re.sub(r"\s+", " ", text)


def corrigir_texto_corrompido(value: Any) -> Any:
    """Corrige mojibake comum apenas quando a conversão reduz seus marcadores.

    Valores já corretos não são recodificados, evitando danificar acentos
    legítimos. Valores não textuais e ausentes são preservados.
    """
    if _is_empty(value) or not isinstance(value, str):
        return value
    original = value
    markers = ("Ã", "Â", "ƒ", "�")
    score_original = sum(original.count(marker) for marker in markers)
    if score_original == 0:
        return original
    for encoding in ("cp1252", "latin1"):
        try:
            candidate = original.encode(encoding).decode("utf-8")
        except (UnicodeDecodeError, UnicodeEncodeError):
            continue
        if sum(candidate.count(marker) for marker in markers) < score_original:
            return candidate
    return original


def limpar_texto(value: Any) -> str:
    """Prepara texto para exibição: corrige codificação e espaços, sem maiúsculas."""
    if _is_empty(value):
        return ""
    text = str(corrigir_texto_corrompido(str(value))).replace("\u00a0", " ")
    return re.sub(r"\s+", " ", text).strip()


def normalizar_texto(value: Any) -> str:
    """Normaliza texto para comparação, preservando a limpeza em ``limpar_texto``."""
    return normalize_name(limpar_texto(value))


def normalizar_codigo_vendedor(value: Any) -> str:
    """Alias em português para a chave canônica do vendedor."""
    return normalize_code(value)


def normalizar_documento(value: Any) -> str:
    """Alias em português para CPF/CNPJ como texto, com zeros preservados."""
    return normalize_cpf_cnpj(value)


def normalizar_data(values: pd.Series) -> pd.Series:
    """Converte datas brasileiras sem interromper o tratamento por valores inválidos."""
    return pd.to_datetime(values, errors="coerce", dayfirst=True)


def normalizar_valor_monetario(values: pd.Series) -> pd.Series:
    """Converte valores brasileiros ou numéricos para ``float`` de modo previsível."""

    def convert(value: Any) -> float:
        if _is_empty(value):
            return 0.0
        text = re.sub(r"[^0-9,.-]", "", str(value)).strip()
        if "," in text:
            text = text.replace(".", "").replace(",", ".")
        try:
            return float(text)
        except ValueError:
            return 0.0

    return values.map(convert).astype(float)


def normalizar_status(value: Any) -> str:
    """Produz uma chave estável para status sem alterar o valor exibido na base."""
    return normalizar_texto(value)

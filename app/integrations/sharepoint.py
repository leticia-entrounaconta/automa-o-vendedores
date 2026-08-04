"""Integração para envio de arquivos ao SharePoint pelo Microsoft Graph."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from urllib.parse import quote

import msal
import requests


GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"


def _obter_variavel(nome: str) -> str:
    valor = os.getenv(nome)

    if not valor:
        raise RuntimeError(
            f"Variável de ambiente obrigatória não configurada: {nome}"
        )

    return valor


def _obter_token() -> str:
    tenant_id = _obter_variavel("MS_TENANT_ID")
    client_id = _obter_variavel("MS_CLIENT_ID")
    client_secret = _obter_variavel("MS_CLIENT_SECRET")

    aplicativo = msal.ConfidentialClientApplication(
        client_id=client_id,
        authority=f"https://login.microsoftonline.com/{tenant_id}",
        client_credential=client_secret,
    )

    resultado = aplicativo.acquire_token_for_client(
        scopes=["https://graph.microsoft.com/.default"]
    )

    token = resultado.get("access_token")

    if not token:
        descricao = resultado.get(
            "error_description",
            "Erro desconhecido ao obter token.",
        )

        raise RuntimeError(
            f"Falha na autenticação Microsoft Graph: {descricao}"
        )

    return token


def _obter_site_id(token: str) -> str:
    hostname = _obter_variavel("SHAREPOINT_HOSTNAME")
    site_path = _obter_variavel("SHAREPOINT_SITE_PATH")

    url = f"{GRAPH_BASE_URL}/sites/{hostname}:{site_path}"

    resposta = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )

    resposta.raise_for_status()

    return resposta.json()["id"]


def _obter_drive_id(token: str, site_id: str) -> str:
    nome_biblioteca = _obter_variavel("SHAREPOINT_LIBRARY")

    url = f"{GRAPH_BASE_URL}/sites/{site_id}/drives"

    resposta = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )

    resposta.raise_for_status()

    for biblioteca in resposta.json().get("value", []):
        if (
            biblioteca.get("name", "").casefold()
            == nome_biblioteca.casefold()
        ):
            return biblioteca["id"]

    raise RuntimeError(
        f"Biblioteca não encontrada: {nome_biblioteca}"
    )


def enviar_arquivo_sharepoint(
    caminho_local: Path,
    nome_remoto: str,
) -> None:
    """Envia ou substitui um arquivo no SharePoint."""

    if not caminho_local.is_file():
        raise FileNotFoundError(
            f"Arquivo local inexistente: {caminho_local}"
        )

    if caminho_local.stat().st_size == 0:
        raise ValueError(
            f"O arquivo local está vazio: {caminho_local}"
        )

    token = _obter_token()
    site_id = _obter_site_id(token)
    drive_id = _obter_drive_id(token, site_id)

    pasta_remota = _obter_variavel(
        "SHAREPOINT_FOLDER"
    ).strip("/")

    caminho_remoto = (
        f"{pasta_remota}/{nome_remoto}"
        if pasta_remota
        else nome_remoto
    )

    caminho_codificado = quote(
        caminho_remoto,
        safe="/",
    )

    url = (
        f"{GRAPH_BASE_URL}/drives/{drive_id}"
        f"/root:/{caminho_codificado}:/content"
    )

    with caminho_local.open("rb") as arquivo:
        resposta = requests.put(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": (
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
            },
            data=arquivo,
            timeout=180,
        )

    resposta.raise_for_status()

    logging.info(
        "Arquivo enviado ao SharePoint: %s",
        caminho_remoto,
    )
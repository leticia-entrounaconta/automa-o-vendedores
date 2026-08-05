"""Upload opcional de relatórios para SharePoint via Microsoft Graph."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from urllib.parse import quote

import requests

from app.settings.environment import ENV_PATH, load_environment

# O arquivo local do projeto tem prioridade sobre variáveis antigas de uma
# sessão do PowerShell ou do Windows. Isso evita combinar credenciais de apps
# distintos na solicitação de token.
load_environment()

logger = logging.getLogger(__name__)
GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
GRAPH_SCOPE = "https://graph.microsoft.com/.default"

SHAREPOINT_ENABLED = os.getenv("SHAREPOINT_ENABLED", "false").strip().lower() == "true"
MS_TENANT_ID = os.getenv("MS_TENANT_ID", "").strip()
MS_CLIENT_ID = os.getenv("MS_CLIENT_ID", "").strip()
MS_CLIENT_SECRET = os.getenv("MS_CLIENT_SECRET", "").strip()


def sharepoint_habilitado() -> bool:
    """Informa se o envio remoto foi habilitado no ambiente atual."""
    return SHAREPOINT_ENABLED


def validar_configuracao_sharepoint() -> None:
    """Valida credenciais sem registrar valores confidenciais."""
    obrigatorias = {
        "MS_TENANT_ID": MS_TENANT_ID,
        "MS_CLIENT_ID": MS_CLIENT_ID,
        "MS_CLIENT_SECRET": MS_CLIENT_SECRET,
    }
    ausentes = [nome for nome, valor in obrigatorias.items() if not valor]
    if ausentes:
        raise RuntimeError(
            "Variáveis obrigatórias do SharePoint ausentes: " + ", ".join(ausentes)
        )
    if len(MS_CLIENT_SECRET) < 10:
        raise RuntimeError("MS_CLIENT_SECRET parece inválido ou incompleto.")


def _registrar_diagnostico_configuracao() -> None:
    """Registra somente metadados seguros para diagnosticar autenticação."""

    logger.info(
        "SharePoint | configuração carregada | env=%s | tenant=%s | client_id=%s | "
        "secret_preenchido=%s | secret_tamanho=%d",
        ENV_PATH,
        MS_TENANT_ID,
        MS_CLIENT_ID,
        bool(MS_CLIENT_SECRET),
        len(MS_CLIENT_SECRET),
    )


def _obter_variavel(nome: str) -> str:
    valor = os.getenv(nome, "").strip()
    if not valor:
        raise RuntimeError(f"Variável do SharePoint não configurada: {nome}")
    return valor


def _detalhe_erro(resposta: requests.Response) -> object:
    try:
        return resposta.json()
    except ValueError:
        return resposta.text


def _validar_resposta(resposta: requests.Response, contexto: str) -> None:
    if resposta.ok:
        return

    detalhe = _detalhe_erro(resposta)
    error_code = None
    if isinstance(detalhe, dict):
        codigos = detalhe.get("error_codes", [])
        if codigos:
            error_code = codigos[0]

    if error_code == 7000215:
        raise RuntimeError(
            "Falha na autenticação do Microsoft Graph: o MS_CLIENT_SECRET é "
            f"inválido para o MS_CLIENT_ID {MS_CLIENT_ID}. Confirme que foi "
            "utilizado o campo 'Value' de um segredo criado no mesmo registro "
            "de aplicativo, e não o Secret ID."
        )

    raise RuntimeError(
        f"Falha ao {contexto} no Microsoft Graph. "
        f"Status: {resposta.status_code}. Detalhe: {detalhe}"
    )


def _obter_token() -> str:
    """Obtém token app-only pelo fluxo client credentials."""
    _registrar_diagnostico_configuracao()
    validar_configuracao_sharepoint()
    token_url = f"https://login.microsoftonline.com/{MS_TENANT_ID}/oauth2/v2.0/token"
    dados = {
        "client_id": MS_CLIENT_ID,
        "client_secret": MS_CLIENT_SECRET,
        "scope": GRAPH_SCOPE,
        "grant_type": "client_credentials",
    }
    resposta = requests.post(token_url, data=dados, timeout=30)
    _validar_resposta(resposta, "obter token de acesso")
    token = resposta.json().get("access_token")
    if not token:
        raise RuntimeError("Microsoft Graph não retornou um token de acesso.")
    return token


def _cabecalho_autorizacao(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _obter_site_id(token: str) -> str:
    hostname = _obter_variavel("SHAREPOINT_HOSTNAME")
    site_path = _obter_variavel("SHAREPOINT_SITE_PATH")
    url = f"{GRAPH_BASE_URL}/sites/{hostname}:{site_path}"
    resposta = requests.get(url, headers=_cabecalho_autorizacao(token), timeout=30)
    _validar_resposta(resposta, "consultar o site")
    return resposta.json()["id"]


def _obter_drive_id(token: str, site_id: str) -> str:
    """Usa a biblioteca padrão quando nenhum nome específico for informado."""
    nome_biblioteca = os.getenv("SHAREPOINT_LIBRARY", "").strip()
    headers = _cabecalho_autorizacao(token)
    if not nome_biblioteca:
        resposta = requests.get(
            f"{GRAPH_BASE_URL}/sites/{site_id}/drive", headers=headers, timeout=30
        )
        _validar_resposta(resposta, "consultar a biblioteca padrão")
        return resposta.json()["id"]

    resposta = requests.get(
        f"{GRAPH_BASE_URL}/sites/{site_id}/drives", headers=headers, timeout=30
    )
    _validar_resposta(resposta, "consultar as bibliotecas")
    for biblioteca in resposta.json().get("value", []):
        if biblioteca.get("name", "").casefold() == nome_biblioteca.casefold():
            return biblioteca["id"]
    raise RuntimeError(f"Biblioteca do SharePoint não encontrada: {nome_biblioteca}")


def _caminho_remoto(nome_remoto: str) -> str:
    pasta = os.getenv("SHAREPOINT_FOLDER", "").strip("/")
    return f"{pasta}/{nome_remoto}" if pasta else nome_remoto


def enviar_arquivo_sharepoint(caminho_local: Path, nome_remoto: str) -> None:
    """Envia ou substitui um arquivo apenas quando o SharePoint estiver habilitado."""
    if not SHAREPOINT_ENABLED:
        logger.info("Integração com SharePoint desabilitada.")
        return
    if not caminho_local.is_file():
        raise FileNotFoundError(f"Arquivo local inexistente: {caminho_local}")
    if caminho_local.stat().st_size == 0:
        raise ValueError(f"O arquivo local está vazio: {caminho_local}")

    token = _obter_token()
    drive_id = _obter_drive_id(token, _obter_site_id(token))
    caminho_remoto = _caminho_remoto(nome_remoto)
    url = f"{GRAPH_BASE_URL}/drives/{drive_id}/root:/{quote(caminho_remoto, safe='/')}:/content"

    with caminho_local.open("rb") as arquivo:
        resposta = requests.put(
            url,
            headers={
                **_cabecalho_autorizacao(token),
                "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            },
            data=arquivo,
            timeout=180,
        )
    _validar_resposta(resposta, "enviar o arquivo")
    logger.info("Arquivo enviado ao SharePoint: %s", caminho_remoto)

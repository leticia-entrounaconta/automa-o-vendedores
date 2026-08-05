"""Testes isolados da integração Microsoft Graph, sem chamadas externas."""

from __future__ import annotations

import importlib


class RespostaFalsa:
    def __init__(self, payload: dict[str, object], status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code
        self.ok = status_code < 400
        self.text = str(payload)

    def json(self) -> dict[str, object]:
        return self._payload


def carregar_sharepoint(monkeypatch, habilitado: bool = True):
    from app.integrations import sharepoint

    sharepoint = importlib.reload(sharepoint)
    configuracao = {
        "SHAREPOINT_ENABLED": str(habilitado).lower(),
        "MS_TENANT_ID": "tenant-test",
        "MS_CLIENT_ID": "client-test",
        "MS_CLIENT_SECRET": "secret-test",
        "SHAREPOINT_HOSTNAME": "entrounaconta.sharepoint.com",
        "SHAREPOINT_SITE_PATH": "/sites/Tienc",
        "SHAREPOINT_LIBRARY": "Documentos",
        "SHAREPOINT_FOLDER": "Bases",
    }
    for nome, valor in configuracao.items():
        monkeypatch.setenv(nome, valor)
    monkeypatch.setattr(sharepoint, "SHAREPOINT_ENABLED", habilitado)
    monkeypatch.setattr(sharepoint, "MS_TENANT_ID", configuracao["MS_TENANT_ID"])
    monkeypatch.setattr(sharepoint, "MS_CLIENT_ID", configuracao["MS_CLIENT_ID"])
    monkeypatch.setattr(sharepoint, "MS_CLIENT_SECRET", configuracao["MS_CLIENT_SECRET"])
    return sharepoint


def test_environment_configuration_is_loaded(monkeypatch) -> None:
    sharepoint = carregar_sharepoint(monkeypatch)
    assert sharepoint.ENV_PATH.name == ".env"
    assert sharepoint.ENV_PATH.is_absolute()
    assert sharepoint.SHAREPOINT_ENABLED
    assert sharepoint.MS_TENANT_ID == "tenant-test"
    sharepoint.validar_configuracao_sharepoint()


def test_disabled_sharepoint_does_not_request_token(monkeypatch, tmp_path) -> None:
    sharepoint = carregar_sharepoint(monkeypatch, habilitado=False)
    monkeypatch.setattr(sharepoint, "_obter_token", lambda: (_ for _ in ()).throw(AssertionError()))
    sharepoint.enviar_arquivo_sharepoint(tmp_path / "ausente.xlsx", "ausente.xlsx")


def test_token_request_uses_client_credentials(monkeypatch) -> None:
    sharepoint = carregar_sharepoint(monkeypatch)
    request_data: dict[str, object] = {}

    def post(url, data, timeout):
        request_data.update({"url": url, "data": data, "timeout": timeout})
        return RespostaFalsa({"access_token": "token-falso"})

    monkeypatch.setattr(sharepoint.requests, "post", post)
    assert sharepoint._obter_token() == "token-falso"
    assert request_data["url"] == "https://login.microsoftonline.com/tenant-test/oauth2/v2.0/token"
    assert request_data["data"]["grant_type"] == "client_credentials"
    assert request_data["data"]["scope"] == "https://graph.microsoft.com/.default"


def test_invalid_client_secret_has_specific_message(monkeypatch) -> None:
    sharepoint = carregar_sharepoint(monkeypatch)
    resposta = RespostaFalsa(
        {"error": "invalid_client", "error_codes": [7000215]},
        status_code=401,
    )

    try:
        sharepoint._validar_resposta(resposta, "obter token de acesso")
    except RuntimeError as error:
        assert "MS_CLIENT_SECRET" in str(error)
        assert "Secret ID" in str(error)
    else:
        raise AssertionError("A resposta AADSTS7000215 deveria falhar.")


def test_site_and_library_lookup_use_expected_endpoints(monkeypatch) -> None:
    sharepoint = carregar_sharepoint(monkeypatch)
    urls: list[str] = []

    def get(url, headers, timeout):
        urls.append(url)
        if url.endswith("/drives"):
            return RespostaFalsa({"value": [{"name": "Documentos", "id": "drive-id"}]})
        return RespostaFalsa({"id": "site-id"})

    monkeypatch.setattr(sharepoint.requests, "get", get)
    token = "token-falso"
    assert sharepoint._obter_site_id(token) == "site-id"
    assert sharepoint._obter_drive_id(token, "site-id") == "drive-id"
    assert urls == [
        "https://graph.microsoft.com/v1.0/sites/entrounaconta.sharepoint.com:/sites/Tienc",
        "https://graph.microsoft.com/v1.0/sites/site-id/drives",
    ]


def test_small_file_upload_uses_destination_folder(monkeypatch, tmp_path) -> None:
    sharepoint = carregar_sharepoint(monkeypatch)
    arquivo = tmp_path / "teste.xlsx"
    arquivo.write_bytes(b"conteudo")
    monkeypatch.setattr(sharepoint, "_obter_token", lambda: "token-falso")
    monkeypatch.setattr(sharepoint, "_obter_site_id", lambda token: "site-id")
    monkeypatch.setattr(sharepoint, "_obter_drive_id", lambda token, site_id: "drive-id")
    envio: dict[str, object] = {}

    def put(url, headers, data, timeout):
        envio.update({"url": url, "headers": headers, "body": data.read(), "timeout": timeout})
        return RespostaFalsa({"id": "arquivo-id"}, status_code=201)

    monkeypatch.setattr(sharepoint.requests, "put", put)
    sharepoint.enviar_arquivo_sharepoint(arquivo, "teste.xlsx")
    assert envio["url"].endswith("/root:/Bases/teste.xlsx:/content")
    assert envio["body"] == b"conteudo"

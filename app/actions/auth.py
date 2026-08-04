import logging

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from app.actions.navigation import open_browser
from app.settings.secrets import (
    login_2tech,
    password_2tech,
    validar_credenciais_2tech,
)
from app.settings.driver_settings import driver, wait


logger = logging.getLogger(__name__)


if not all([login_2tech, password_2tech]):
    logger.error(
        "As variáveis de ambiente USUARIO_2TECH/LOGIN2TECH e SENHA_2TECH/PASSWORD2TECH não foram configuradas."
    )


@open_browser
def make_login():
    make_login_2tech()


def make_login_2tech():
    validar_credenciais_2tech()

    logger.info("Preenchendo usuário")

    usuario = wait.until(
        EC.visibility_of_element_located((By.ID, "txtUsuario"))
    )
    usuario.clear()
    usuario.send_keys(login_2tech)

    logger.info("Preenchendo senha")

    senha = wait.until(
        EC.visibility_of_element_located((By.ID, "txtSenha"))
    )
    senha.clear()
    senha.send_keys(password_2tech)

    logger.info("Clicando em Entrar")

    botao_login = wait.until(
        EC.element_to_be_clickable((By.ID, "btnLogin"))
    )
    botao_login.click()

    wait.until(lambda current_driver: current_driver.execute_script("return document.readyState") == "complete")
    logger.info("Login 2Tech concluído")

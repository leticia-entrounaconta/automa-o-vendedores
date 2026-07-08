import logging
from time import sleep

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from app.actions.navigation import open_browser
from app.settings.secrets import (
    login,
    login_2tech,
    password,
    password_2tech,
)
from app.settings.driver_settings import driver, wait


logger = logging.getLogger(__name__)


if not all([login, login_2tech, password, password_2tech]):
    logger.error(
        "Environment variables LOGIN_2TECH, LOGIN, PASSWORD_2TECH or PASSWORD are not set."
    )


@open_browser
def make_login():
    make_login_2tech()


def make_login_2tech():
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

    logger.info("Aguardando carregamento da página")

    sleep(2)
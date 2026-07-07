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


if not all([login, login_2tech, password, password_2tech]):
    logging.error(
        "Environment variables LOGIN_2TECH, LOGIN, PASSWORD_2TECH or PASSWORD are not set."
    )


@open_browser
def make_login():
    wait.until(
        EC.visibility_of_element_located((By.ID, "txtUsuario"))
    ).send_keys(login_2tech)

    wait.until(
        EC.visibility_of_element_located((By.ID, "txtSenha"))
    ).send_keys(password_2tech)

    wait.until(
        EC.element_to_be_clickable((By.ID, "btnLogin"))
    ).click()

    sleep(2)


def make_login_2tech():
    # login 2tech
    wait.until(EC.visibility_of_element_located((By.ID, "txtUsuario"))).send_keys(login_2tech)
    driver.find_element(By.ID, "txtSenha").send_keys(password_2tech)
 
    driver.find_element(By.ID, "btnLogin").click()

    sleep(2)
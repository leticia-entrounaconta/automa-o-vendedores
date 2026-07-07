import logging

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from app.actions.navigation import open_browser
from app.settings.secrets import login, login_2tech, password, password_2tech
from app.settings.driver_settings import driver, wait
from time import sleep

if not all([login, login_2tech, password, password_2tech]):
    logging.error("Environment variables LOGIN_2TECH, LOGIN, PASSWORD_2TECH or PASSWORD are not set.")


@open_browser
def make_login():
    wait.until(
        EC.visibility_of_element_located((By.ID, "login"))
    ).send_keys(login)

    wait.until(
        EC.visibility_of_element_located((By.ID, "password"))
    ).send_keys(password)

    wait.until(
        EC.element_to_be_clickable((By.ID, "btnLogin"))
    ).click()

    sleep(2)


def make_login_2tech():
    wait.until(
        EC.visibility_of_element_located((By.ID, "login"))
    ).send_keys(login_2tech)

    wait.until(
        EC.visibility_of_element_located((By.ID, "password"))
    ).send_keys(password_2tech)

    wait.until(
        EC.element_to_be_clickable((By.ID, "btnLogin"))
    ).click()

    sleep(2)
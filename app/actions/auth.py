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
    pass
    # login


def make_login_2tech():
    pass
    # login 2tech
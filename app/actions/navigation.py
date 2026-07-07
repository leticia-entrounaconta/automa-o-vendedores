import logging
from functools import wraps

from app.settings.config import BASE_URL, BASE_URL_2TECH
from app.settings.driver_settings import driver, wait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from time import sleep

logger = logging.getLogger(__name__)


def open_browser(func):
    """Decorator that navigates to TARGET_URL before executing the wrapped function."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.info("Navegando para %s", BASE_URL)
        driver.get(BASE_URL)
        return func(*args, **kwargs)

    return wrapper


def navigate_to(url: str):
    """Navigate the browser to a specific URL."""
    logger.info("Navegando para %s", url)
    driver.get(url)

def navigate_to_system():
    driver.get(f"{BASE_URL_2TECH}default.asp")
    
def switch_to_window(index: int = 0):
    """Switch to a browser window by index."""
    handles = driver.window_handles
    if index < len(handles):
        driver.switch_to.window(handles[index])
        logger.debug("Switched to window %d", index)
    else:
        logger.warning("Window index %d nao existe (total: %d)", index, len(handles))

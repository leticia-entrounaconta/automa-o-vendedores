import logging
from functools import wraps

from selenium.common import (
    ElementClickInterceptedException,
    InvalidArgumentException,
    NoSuchElementException,
    NoSuchWindowException,
    TimeoutException,
    WebDriverException,
)


def handle_selenium_exceptions(func):
    """Decorator that catches common Selenium exceptions and logs them."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (
            InvalidArgumentException,
            TimeoutException,
            NoSuchWindowException,
            WebDriverException,
            NoSuchElementException,
            ElementClickInterceptedException,
        ) as e:
            _log_exception(e)
            raise

    return wrapper


def _log_exception(ex: Exception):
    logging.exception(
        "Error! Exception Type: %s | Message: %s",
        type(ex).__name__,
        str(ex),
    )

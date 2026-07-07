import logging

from app.data_processing.exception_handler import handle_selenium_exceptions
from app.settings import driver

logger = logging.getLogger(__name__)


@handle_selenium_exceptions
def handle_cookies():
    """Dismiss cookie consent banner if present."""
    try:
        cookie_btn = driver.find_element("css selector", "[id*='cookie'] button, .cookie-accept")
        cookie_btn.click()
        logger.info("Cookie banner dismissed.")
    except Exception:
        logger.debug("No cookie banner found.")

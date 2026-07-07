import logging
import os
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from app.settings.config import DOWNLOAD_PATH, ELEMENT_WAIT_TIMEOUT, EXPLICITLY_WAIT, PAGE_LOAD_TIMEOUT


def get_chrome_options() -> Options:
    """Returns Chrome options configured with standard arguments and download preferences."""
    options = Options()
    arguments = [
        "--start-maximized",
        "--disable-dev-shm-usage",
        "--no-sandbox",
        "--disable-gpu",
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    ]
    for arg in arguments:
        options.add_argument(arg)

    prefs = {
        "download.default_directory": DOWNLOAD_PATH,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }
    options.add_experimental_option("prefs", prefs)

    enable_vnc = os.getenv("ENABLE_VNC", "true").lower()
    if enable_vnc in ("0", "false", "no", "off"):
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1280,720")

    chrome_binary = os.getenv("CHROME_BINARY")
    if chrome_binary:
        options.binary_location = chrome_binary

    return options


def initialize_webdriver() -> webdriver.Chrome:
    """Initializes and returns a Chrome WebDriver instance."""
    options = get_chrome_options()

    try:
        return webdriver.Chrome(options=options)
    except Exception as exc:
        logging.warning("Falling back to webdriver_manager ChromeDriver: %s", exc)

    driver_path = ChromeDriverManager().install()
    service = ChromeService(driver_path)
    return webdriver.Chrome(service=service, options=options)


def create_driver() -> tuple[webdriver.Chrome, WebDriverWait]:
    """Create a configured WebDriver + WebDriverWait pair."""
    try:
        driver_instance = initialize_webdriver()
        wait_instance = WebDriverWait(driver_instance, timeout=EXPLICITLY_WAIT)
        driver_instance.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
        driver_instance.implicitly_wait(ELEMENT_WAIT_TIMEOUT)
        return driver_instance, wait_instance
    except WebDriverException as wde:
        logging.exception("Failed to initialize webDriver: %s", wde)
        raise
    except Exception as exc:
        logging.exception("Unexpected error while initializing webDriver: %s", exc)
        raise


driver, wait = create_driver()

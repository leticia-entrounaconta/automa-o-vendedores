import logging
from time import sleep

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from app.settings.driver_settings import driver, wait
from app.data_processing.date_handler import date_today, date_fifteen_days_ago
from app.data_processing.excel_handler import wait_download


logger = logging.getLogger(__name__)


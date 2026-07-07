from datetime import date, datetime, timedelta

import holidays


def is_weekend(d: date) -> bool:
    return d.weekday() >= 5


def is_holiday(d: date, country: str = "BR") -> bool:
    return d in holidays.country_holidays(country)


def is_business_day(d: date) -> bool:
    return not is_weekend(d) and not is_holiday(d)


def get_last_business_day(reference: date | None = None) -> date:
    """Retorna o último dia útil."""
    d = reference or date.today()

    while not is_business_day(d):
        d -= timedelta(days=1)

    return d


def get_previous_business_day(reference: date | None = None) -> date:
    """Retorna o dia útil anterior."""
    d = (reference or date.today()) - timedelta(days=1)

    while not is_business_day(d):
        d -= timedelta(days=1)

    return d


def get_fifteen_days_before(reference: date | None = None) -> date:
    """Retorna o dia útil de quinze dias atrás."""
    d = (reference or date.today()) - timedelta(days=15)

    while not is_business_day(d):
        d -= timedelta(days=1)

    return d


def today():
    return date.today()


def today_str():
    return date.today().strftime("%d/%m/%Y")


def now_str():
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")


def file_timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def excel_date():
    return datetime.now().strftime("%d-%m-%Y")


# Datas prontas para utilização
date_today = today_str()
date_yesterday = get_previous_business_day().strftime("%d/%m/%Y")
date_fifteen_days_ago = get_fifteen_days_before().strftime("%d/%m/%Y")
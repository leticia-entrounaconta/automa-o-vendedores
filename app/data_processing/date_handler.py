from datetime import date, timedelta
import holidays

def is_weekend(d: date) -> bool:
    return d.weekday() >= 5


def is_holiday(d: date, country: str = "BR") -> bool:
    return d in holidays.country_holidays(country)


def is_business_day(d: date) -> bool:
    return not is_weekend(d) and not is_holiday(d)


def get_last_business_day(reference: date | None = None) -> date:
    """Return the most recent business day on or before *reference*."""
    d = reference or date.today()
    while not is_business_day(d):
        d -= timedelta(days=1)
    return d


def get_previous_business_day(reference: date | None = None) -> date:
    """Return the business day immediately before *reference*."""
    d = (reference or date.today()) - timedelta(days=1)
    while not is_business_day(d):
        d -= timedelta(days=1)
    return d

def get_fifteen_days_before(reference: date | None = None) -> date:
    """Return the business day fifteen days before *reference*."""
    d = (reference or date.today()) - timedelta(days=15)
    while not is_business_day(d):
        d -= timedelta(days=1)
    return d


# Pre-computed convenience dates
date_today = date.today().strftime("%d/%m/%Y")
date_yesterday = get_previous_business_day().strftime("%d/%m/%Y")
date_fifteen_days_ago = get_fifteen_days_before().strftime("%d/%m/%Y")

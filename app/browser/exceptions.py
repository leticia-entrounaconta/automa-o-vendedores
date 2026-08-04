"""Specific errors raised by the browser automation."""


class AutomationError(RuntimeError):
    """Base error for an actionable automation failure."""


class NavigationError(AutomationError):
    """The application could not reach the requested page."""


class ExportError(AutomationError):
    """A report export could not be initiated."""


class DownloadError(AutomationError):
    """A downloaded file is missing, incomplete or invalid."""


class ReportValidationError(AutomationError):
    """A report file does not satisfy the expected minimum structure."""

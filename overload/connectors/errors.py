# exceptions specific to overload


class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class APISettingsError(Error):
    """Exception raised when API connection is incomplete"""
    pass


class ExceededLimitsError(Error):
    """Exception raised when Sierra API endpoint requests
    exceeded its limits"""
    pass


class APICriticalError(Error):
    """Exception raised when received API response includes
    one of the critical error codes that grant termination
    of Sierra queries all together"""
    pass


class APITimeoutError(Error):
    """Exception wrapper for requests.exceptions.Timeout,
    raised when aloted time passed without API response"""
    pass


class APITokenError(Error):
    """Exception wrapper for oauthlib.oauth2.MissingTokenError
    raised when Sierra API token is not obtained
    """


class UnhandledException(Error):
    """Unhandled exception encounted. Raise to catch for
    fixing"""
    pass

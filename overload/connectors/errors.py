# -*- coding: utf-8 -*-

"""
connectors.errors
~~~~~~~~~~~~~~~~~~~
This module contains the set of Overload's exceptions.
"""


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
    """Exception raised when aloted time passed without API response"""
    pass


class APITokenError(Error):
    """Exception raised when Sierra API token is not obtained
    """


class APITokenExpired(Error):
    """Exception raised when API access token appears to be expired
    """
    pass


class UnhandledException(Error):
    """Unhandled exception encounted. Raise to catch for
    fixing"""
    pass

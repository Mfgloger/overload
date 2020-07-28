# -*- coding: utf-8 -*-

"""
overload.exceptions
~~~~~~~~~~~~~~~~~~~
This module contains the set of Overload's exceptions.
"""


class OverloadError(Exception):
    """Base class for exceptions in this module."""

    pass


class ExceededLimitsError(OverloadError):
    """Exception raised when Sierra API endpoint requests
    exceeded its limits"""

    pass


class APICriticalError(OverloadError):
    """Exception raised when received API response includes
    one of the critical error codes that grant termination
    of Sierra queries all together"""

    pass


class APITimeoutError(OverloadError):
    """Exception raised when aloted time passed without API response"""

    pass


class APITokenError(OverloadError):
    """Exception raised when Sierra API token is not obtained
    """

    pass


class APITokenExpiredError(OverloadError):
    """Exception raised when API access token appears to be expired
    """

    pass


class UnhandledException(OverloadError):
    """Unhandled exception encounted. Raise to catch for
    fixing"""

    pass

class ConnectionFailed(Exception):
    """Raised by Service instances when connection fails, used for tracking failures.

    """
    pass


class ConfigurationError(Exception):
    """Used for exceptions related to connection and flow control parameters.

    """
    pass


class DataError(Exception):
    """Used for all credential data related exceptions.

    """
    pass

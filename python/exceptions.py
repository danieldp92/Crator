class InvalidURLException(Exception):
    pass


class InvalidCookieException(Exception):
    pass


class UnknownProxyProtocolException(Exception):
    pass


class RedirectPageException(Exception):
    pass


class HTTPStatusCodeError(Exception):
    def __init__(self, status_code):
        self.status_code = status_code
        super().__init__(f"HTTP status code error: {status_code}")
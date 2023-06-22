
"""
Functions to simplify working with urls
"""

from urllib.parse import urlparse, urlunsplit


def ensure_is_absolute(url: str, host: str):
    """
    Ensures the provided url is absolute. If not it uses the provided host to form an absolute url
    """
    is_absolute = bool(urlparse(url).netloc)
    if is_absolute:
        return url
    # TODO write test that this includes fragments and queries
    return urlunsplit(("https", host, url, "", ""))

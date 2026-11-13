"""
Library provider abstraction.

Reads LIBRARY_PROVIDER from config and routes upstream API requests to either
the Calibre server or the Talebook server accordingly.

Usage:
    from utils.library_provider import get_provider, is_talebook, library_request

    # Make a GET request to /ajax/book/123 on whichever backend is active:
    response = library_request('GET', '/ajax/book/123')
"""

import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
import config_manager


def get_provider():
    """Return the active library provider name ('calibre' or 'talebook')."""
    return (config_manager.config.get('LIBRARY_PROVIDER') or 'calibre').lower()


def is_talebook():
    """Return True when the active provider is Talebook."""
    return get_provider() == 'talebook'


def get_base_url():
    """Return the base URL for the active provider, with trailing slash removed."""
    if is_talebook():
        return (config_manager.config.get('TALEBOOK_URL') or '').rstrip('/')
    return (config_manager.config.get('CALIBRE_URL') or '').rstrip('/')


def _get_credentials(username_key, password_key):
    """Return (username, password) tuple from config, or (None, None) if either is absent."""
    username = config_manager.config.get(username_key) or None
    password = config_manager.config.get(password_key) or None
    return username, password


def get_auth():
    """Return an auth object appropriate for the active provider."""
    if is_talebook():
        username, password = _get_credentials('TALEBOOK_USERNAME', 'TALEBOOK_PASSWORD')
        if username and password:
            return HTTPBasicAuth(username, password)
        return None
    # Calibre uses HTTP Digest Auth
    username, password = _get_credentials('CALIBRE_USERNAME', 'CALIBRE_PASSWORD')
    if username and password:
        return HTTPDigestAuth(username, password)
    return None


def get_timeout():
    """Return the request timeout for the active provider (seconds)."""
    if is_talebook():
        try:
            return int(config_manager.config.get('TALEBOOK_TIMEOUT') or 15)
        except (ValueError, TypeError):
            return 15
    return 15


def get_verify_ssl():
    """Return the SSL verification setting for the active provider."""
    if is_talebook():
        val = config_manager.config.get('TALEBOOK_VERIFY_SSL')
        if val is None:
            return True
        return bool(val)
    return True


def library_request(method, path, **kwargs):
    """
    Make an HTTP request to the active library provider.

    :param method: HTTP method string, e.g. 'GET', 'POST'.
    :param path:   URL path (starting with '/'), e.g. '/ajax/book/123'.
    :param kwargs: Any extra keyword arguments accepted by requests.request().
    :return:       requests.Response object.
    """
    url = f"{get_base_url()}{path}"
    kwargs.setdefault('auth', get_auth())
    kwargs.setdefault('timeout', get_timeout())
    kwargs.setdefault('verify', get_verify_ssl())
    return requests.request(method, url, **kwargs)

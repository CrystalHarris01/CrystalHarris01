"""Tiny JSON-over-HTTP helper built on the standard library only."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

USER_AGENT = "bookfinder/0.1 (legal-access aggregator; +https://example.org)"
TIMEOUT = 15


def get_json(url: str, params: dict | None = None) -> dict | list | None:
    """GET a URL and parse JSON. Returns None on any network/parse error.

    Errors are swallowed deliberately: one source being down should never
    stop the others from returning useful results.
    """
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            return json.loads(resp.read().decode(charset))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError,
            json.JSONDecodeError, ValueError):
        return None

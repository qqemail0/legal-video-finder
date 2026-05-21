from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Iterable


class HttpClientError(RuntimeError):
    pass


def get_json(url: str, params: dict[str, str] | Iterable[tuple[str, str]] | None = None, timeout: int = 12):
    if params:
        query = urllib.parse.urlencode(params)
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}{query}"
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "LegalVideoFinder/0.1 (+https://github.com/qqemail0/legal-video-finder)",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            payload = response.read().decode(charset, errors="replace")
    except Exception as exc:  # pragma: no cover - network branch
        raise HttpClientError(str(exc)) from exc

    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        raise HttpClientError(f"Invalid JSON from {url}") from exc


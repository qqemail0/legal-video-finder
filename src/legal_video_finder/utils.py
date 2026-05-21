from __future__ import annotations

import html
import re
import unicodedata
from difflib import SequenceMatcher
from typing import Iterable


def normalize_title(value: str) -> str:
    text = unicodedata.normalize("NFKC", value or "").casefold()
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[^\w\u4e00-\u9fff]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def strip_html(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def score_match(query: str, title: str, aliases: Iterable[str] = ()) -> float:
    normalized_query = normalize_title(query)
    candidates = [normalize_title(title), *(normalize_title(alias) for alias in aliases)]
    candidates = [candidate for candidate in candidates if candidate]
    if not normalized_query or not candidates:
        return 0.0

    best = 0.0
    for candidate in candidates:
        ratio = SequenceMatcher(None, normalized_query, candidate).ratio()
        if candidate == normalized_query:
            ratio = 1.0
        elif normalized_query in candidate or candidate in normalized_query:
            ratio = max(ratio, 0.82)
        best = max(best, ratio)
    return round(best * 100, 2)


def clamp_score(value: float) -> float:
    return round(max(0.0, min(100.0, value)), 2)


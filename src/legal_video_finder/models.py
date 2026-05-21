from __future__ import annotations

from dataclasses import dataclass, field

from .utils import normalize_title


@dataclass(frozen=True)
class VideoResult:
    title: str
    provider: str
    kind: str
    year: str = ""
    description: str = ""
    watch_url: str = ""
    source_url: str = ""
    thumbnail_url: str = ""
    confidence: float = 0.0
    legal_status: str = "metadata"
    legal_note: str = ""
    tags: tuple[str, ...] = field(default_factory=tuple)

    @property
    def primary_url(self) -> str:
        return self.watch_url or self.source_url

    @property
    def dedupe_key(self) -> tuple[str, str]:
        return normalize_title(self.title), str(self.year or "")


@dataclass(frozen=True)
class SearchOutcome:
    results: list[VideoResult]
    errors: list[str] = field(default_factory=list)


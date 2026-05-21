from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from .http_client import HttpClientError, get_json
from .models import VideoResult
from .utils import clamp_score, score_match, strip_html


class ProviderError(RuntimeError):
    pass


class SearchProvider(Protocol):
    name: str

    def search(self, query: str, limit: int = 8) -> list[VideoResult]:
        ...


class BuiltInLegalCatalogProvider:
    name = "内置合法片库"

    def __init__(self, catalog_path: Path):
        self.catalog_path = catalog_path

    def search(self, query: str, limit: int = 8) -> list[VideoResult]:
        items = _read_json_list(self.catalog_path)
        results: list[VideoResult] = []
        for item in items:
            aliases = tuple(item.get("aliases", []))
            confidence = score_match(query, item.get("title", ""), aliases)
            haystack = " ".join([item.get("title", ""), item.get("description", ""), " ".join(aliases), " ".join(item.get("tags", []))])
            if confidence < 45 and query.casefold() not in haystack.casefold():
                continue
            results.append(_video_from_json(item, self.name, confidence))
        return sorted(results, key=lambda result: result.confidence, reverse=True)[:limit]


class CustomJsonProvider:
    name = "自定义合法源"

    def __init__(self, source_path: Path):
        self.source_path = source_path

    def search(self, query: str, limit: int = 8) -> list[VideoResult]:
        if not self.source_path.exists():
            return []
        items = _read_json_list(self.source_path)
        results: list[VideoResult] = []
        for item in items:
            confidence = score_match(query, item.get("title", ""), item.get("aliases", []))
            haystack = " ".join([item.get("title", ""), item.get("description", ""), " ".join(item.get("tags", []))])
            if confidence < 45 and query.casefold() not in haystack.casefold():
                continue
            results.append(_video_from_json(item, self.name, confidence))
        return sorted(results, key=lambda result: result.confidence, reverse=True)[:limit]


class InternetArchiveProvider:
    name = "Internet Archive"

    def search(self, query: str, limit: int = 8) -> list[VideoResult]:
        params = [
            ("q", f'({query}) AND mediatype:(movies)'),
            ("fl[]", "identifier"),
            ("fl[]", "title"),
            ("fl[]", "description"),
            ("fl[]", "year"),
            ("fl[]", "collection"),
            ("sort[]", "downloads desc"),
            ("rows", str(limit)),
            ("page", "1"),
            ("output", "json"),
        ]
        try:
            payload = get_json("https://archive.org/advancedsearch.php", params)
        except HttpClientError as exc:  # pragma: no cover - network branch
            raise ProviderError(f"{self.name}: {exc}") from exc

        docs = payload.get("response", {}).get("docs", [])
        results: list[VideoResult] = []
        for doc in docs:
            identifier = doc.get("identifier", "")
            title = doc.get("title") or identifier
            url = f"https://archive.org/details/{identifier}" if identifier else "https://archive.org"
            collections = doc.get("collection") or []
            if isinstance(collections, str):
                collections = [collections]
            results.append(
                VideoResult(
                    title=title,
                    provider=self.name,
                    kind="公共档案视频",
                    year=str(doc.get("year") or ""),
                    description=strip_html(doc.get("description", ""))[:600],
                    watch_url=url,
                    source_url=url,
                    confidence=score_match(query, title),
                    legal_status="archive-public-access",
                    legal_note="来自 Internet Archive 的公开视频档案；具体版权和地区限制以原页面说明为准。",
                    tags=tuple(str(item) for item in collections[:5]),
                )
            )
        return results


class JikanAnimeProvider:
    name = "Jikan Anime"

    def search(self, query: str, limit: int = 8) -> list[VideoResult]:
        try:
            payload = get_json("https://api.jikan.moe/v4/anime", {"q": query, "limit": str(limit)})
        except HttpClientError as exc:  # pragma: no cover - network branch
            raise ProviderError(f"{self.name}: {exc}") from exc

        results: list[VideoResult] = []
        for item in payload.get("data", []):
            title = item.get("title") or item.get("title_english") or "Untitled"
            trailer = item.get("trailer") or {}
            trailer_url = trailer.get("url") or ""
            images = item.get("images") or {}
            jpg = images.get("jpg") or {}
            aliases = [item.get("title_english", ""), item.get("title_japanese", "")]
            results.append(
                VideoResult(
                    title=title,
                    provider=self.name,
                    kind=f"动漫 / {item.get('type') or 'Anime'}",
                    year=str(item.get("year") or ""),
                    description=strip_html(item.get("synopsis", ""))[:600],
                    watch_url=trailer_url or item.get("url", ""),
                    source_url=item.get("url", ""),
                    thumbnail_url=jpg.get("image_url", ""),
                    confidence=score_match(query, title, aliases),
                    legal_status="metadata-trailer",
                    legal_note="Jikan 提供动漫元数据和预告片入口，不提供正片盗版播放源。",
                    tags=tuple(genre.get("name", "") for genre in item.get("genres", []) if genre.get("name")),
                )
            )
        return results


class TVMazeProvider:
    name = "TVmaze"

    def search(self, query: str, limit: int = 8) -> list[VideoResult]:
        try:
            payload = get_json("https://api.tvmaze.com/search/shows", {"q": query})
        except HttpClientError as exc:  # pragma: no cover - network branch
            raise ProviderError(f"{self.name}: {exc}") from exc

        results: list[VideoResult] = []
        for entry in payload[:limit]:
            show = entry.get("show") or {}
            title = show.get("name") or "Untitled"
            premiered = show.get("premiered") or ""
            year = premiered[:4] if premiered else ""
            image = show.get("image") or {}
            api_score = float(entry.get("score") or 0) * 100
            exact_score = score_match(query, title)
            results.append(
                VideoResult(
                    title=title,
                    provider=self.name,
                    kind="剧集 / TV",
                    year=year,
                    description=strip_html(show.get("summary", ""))[:600],
                    watch_url=show.get("officialSite") or show.get("url", ""),
                    source_url=show.get("url", ""),
                    thumbnail_url=image.get("medium", ""),
                    confidence=clamp_score(max(api_score, exact_score)),
                    legal_status="metadata-official-link",
                    legal_note="TVmaze 提供剧集元数据；观看入口优先使用官方站点或 TVmaze 页面。",
                    tags=tuple(show.get("genres") or ()),
                )
            )
        return results


def create_default_providers(data_dir: Path) -> list[SearchProvider]:
    return [
        BuiltInLegalCatalogProvider(data_dir / "legal_catalog.json"),
        CustomJsonProvider(data_dir / "custom_sources.json"),
        InternetArchiveProvider(),
        JikanAnimeProvider(),
        TVMazeProvider(),
    ]


def _read_json_list(path: Path) -> list[dict]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as exc:
        raise ProviderError(f"JSON 格式错误: {path.name}") from exc
    if not isinstance(payload, list):
        raise ProviderError(f"{path.name} 必须是 JSON 数组")
    return [item for item in payload if isinstance(item, dict)]


def _video_from_json(item: dict, provider: str, confidence: float) -> VideoResult:
    return VideoResult(
        title=item.get("title", "Untitled"),
        provider=provider,
        kind=item.get("kind", "视频"),
        year=str(item.get("year", "")),
        description=item.get("description", ""),
        watch_url=item.get("watch_url", ""),
        source_url=item.get("source_url", item.get("watch_url", "")),
        thumbnail_url=item.get("thumbnail_url", ""),
        confidence=confidence,
        legal_status=item.get("legal_status", "user-provided"),
        legal_note=item.get("legal_note", "用户自定义合法来源，请自行确认授权范围。"),
        tags=tuple(item.get("tags", [])),
    )


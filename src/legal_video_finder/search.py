from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed

from .models import SearchOutcome, VideoResult
from .providers import ProviderError, SearchProvider


class SearchEngine:
    def __init__(self, providers: list[SearchProvider]):
        self.providers = providers

    def search(self, query: str, limit_per_provider: int = 8) -> SearchOutcome:
        query = query.strip()
        if not query:
            return SearchOutcome([])

        results: list[VideoResult] = []
        errors: list[str] = []
        with ThreadPoolExecutor(max_workers=min(6, max(1, len(self.providers)))) as executor:
            future_map = {
                executor.submit(provider.search, query, limit_per_provider): provider
                for provider in self.providers
            }
            for future in as_completed(future_map):
                provider = future_map[future]
                try:
                    results.extend(future.result())
                except ProviderError as exc:
                    errors.append(str(exc))
                except Exception as exc:  # pragma: no cover - defensive branch
                    errors.append(f"{provider.name}: {exc}")

        return SearchOutcome(_dedupe_and_rank(results), errors)


def _dedupe_and_rank(results: list[VideoResult]) -> list[VideoResult]:
    by_key: dict[tuple[str, str], VideoResult] = {}
    for result in results:
        key = result.dedupe_key
        current = by_key.get(key)
        if current is None or result.confidence > current.confidence:
            by_key[key] = result
    return sorted(by_key.values(), key=lambda item: (item.confidence, bool(item.watch_url)), reverse=True)


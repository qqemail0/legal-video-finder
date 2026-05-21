from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from legal_video_finder.models import VideoResult
from legal_video_finder.providers import CustomJsonProvider
from legal_video_finder.search import SearchEngine
from legal_video_finder.store import AppStore
from legal_video_finder.utils import normalize_title, score_match


class FakeProvider:
    def __init__(self, name: str, results: list[VideoResult]):
        self.name = name
        self._results = results

    def search(self, query: str, limit: int = 8) -> list[VideoResult]:
        return self._results[:limit]


class CoreTests(unittest.TestCase):
    def test_normalize_and_score_exact_titles(self):
        self.assertEqual(normalize_title("  Big-Buck_Bunny!! "), "big buck_bunny")
        self.assertGreaterEqual(score_match("Sintel", "Sintel"), 99)
        self.assertGreater(score_match("活死人", "活死人之夜"), 70)

    def test_search_engine_dedupes_by_title_and_year(self):
        low = VideoResult(title="Sintel", provider="A", kind="动画", year="2010", confidence=65, watch_url="https://a.example")
        high = VideoResult(title="Sintel", provider="B", kind="动画", year="2010", confidence=96, watch_url="https://b.example")
        engine = SearchEngine([FakeProvider("A", [low]), FakeProvider("B", [high])])
        outcome = engine.search("Sintel")
        self.assertEqual(len(outcome.results), 1)
        self.assertEqual(outcome.results[0].provider, "B")

    def test_custom_json_provider_loads_authorized_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "custom_sources.json"
            path.write_text(
                json.dumps(
                    [
                        {
                            "title": "Authorized Anime",
                            "aliases": ["合法动漫"],
                            "kind": "动画",
                            "watch_url": "https://example.com/watch",
                            "legal_status": "user-authorized",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            results = CustomJsonProvider(path).search("合法动漫")
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].legal_status, "user-authorized")

    def test_store_favorites_and_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = AppStore(Path(tmp) / "app.db")
            item = VideoResult(title="Sintel", provider="Test", kind="动画", watch_url="https://example.com/sintel")
            store.add_history("sintel")
            store.add_favorite(item)
            self.assertEqual(store.list_history()[0][0], "sintel")
            self.assertEqual(store.list_favorites()[0].title, "Sintel")
            store.remove_favorite("https://example.com/sintel")
            self.assertEqual(store.list_favorites(), [])


if __name__ == "__main__":
    unittest.main()


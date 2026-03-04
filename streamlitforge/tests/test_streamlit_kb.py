"""Tests for StreamlitKnowledgeBase — no mocks, real functional calls."""

import json
import os
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

from streamlitforge.knowledge.streamlit_kb import StreamlitKnowledgeBase


class TestStreamlitKnowledgeBaseInit(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.cache_path = os.path.join(self.tmp, "knowledge")
        self.kb = StreamlitKnowledgeBase(cache_path=self.cache_path)

    def test_cache_dir_created(self):
        self.assertTrue(Path(self.cache_path).is_dir())

    def test_default_cache_expiry(self):
        self.assertEqual(self.kb.cache_expiry, 24)

    def test_custom_cache_expiry(self):
        kb = StreamlitKnowledgeBase(cache_path=self.cache_path, cache_expiry_hours=48)
        self.assertEqual(kb.cache_expiry, 48)


class TestBuiltinFeatures(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.kb = StreamlitKnowledgeBase(cache_path=os.path.join(self.tmp, "kb"))

    def test_builtin_features_has_version(self):
        features = self.kb._get_builtin_features()
        self.assertIn("version", features)
        self.assertEqual(features["version"], "1.41.0")

    def test_builtin_features_has_chat(self):
        features = self.kb._get_builtin_features()
        self.assertIn("chat", features["features"])
        self.assertIn("st.chat_message", features["features"]["chat"])

    def test_builtin_features_has_data(self):
        features = self.kb._get_builtin_features()
        self.assertIn("data", features["features"])
        self.assertIn("st.dataframe", features["features"]["data"])

    def test_builtin_features_has_input_widgets(self):
        features = self.kb._get_builtin_features()
        self.assertIn("input", features["features"])
        self.assertGreater(len(features["features"]["input"]), 5)

    def test_builtin_features_has_layout(self):
        features = self.kb._get_builtin_features()
        self.assertIn("layout", features["features"])
        self.assertIn("st.columns", features["features"]["layout"])

    def test_builtin_features_has_deprecations(self):
        features = self.kb._get_builtin_features()
        self.assertIsInstance(features["deprecations"], list)
        self.assertGreater(len(features["deprecations"]), 0)

    def test_builtin_features_has_best_practices(self):
        features = self.kb._get_builtin_features()
        self.assertIsInstance(features["best_practices"], list)
        self.assertGreater(len(features["best_practices"]), 0)


class TestCacheValidity(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.cache_path = os.path.join(self.tmp, "kb")
        self.kb = StreamlitKnowledgeBase(cache_path=self.cache_path)

    def test_nonexistent_cache_is_invalid(self):
        fake = Path(self.cache_path) / "nonexistent.json"
        self.assertFalse(self.kb._is_cache_valid(fake))

    def test_valid_cache_within_expiry(self):
        cache_file = Path(self.cache_path) / "test_cache.json"
        cache_file.write_text(json.dumps({
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "data": {"version": "1.41.0"},
        }))
        self.assertTrue(self.kb._is_cache_valid(cache_file))

    def test_expired_cache(self):
        cache_file = Path(self.cache_path) / "test_expired.json"
        old_time = datetime.now(timezone.utc) - timedelta(hours=48)
        cache_file.write_text(json.dumps({
            "fetched_at": old_time.isoformat(),
            "data": {},
        }))
        self.assertFalse(self.kb._is_cache_valid(cache_file))

    def test_custom_hours_parameter(self):
        cache_file = Path(self.cache_path) / "test_hours.json"
        recent = datetime.now(timezone.utc) - timedelta(hours=2)
        cache_file.write_text(json.dumps({
            "fetched_at": recent.isoformat(),
            "data": {},
        }))
        self.assertTrue(self.kb._is_cache_valid(cache_file, hours=6))
        self.assertFalse(self.kb._is_cache_valid(cache_file, hours=1))

    def test_corrupt_cache_is_invalid(self):
        cache_file = Path(self.cache_path) / "corrupt.json"
        cache_file.write_text("not json at all!")
        self.assertFalse(self.kb._is_cache_valid(cache_file))

    def test_missing_fetched_at_is_invalid(self):
        cache_file = Path(self.cache_path) / "no_ts.json"
        cache_file.write_text(json.dumps({"data": {}}))
        self.assertFalse(self.kb._is_cache_valid(cache_file))


class TestSearchExamples(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.kb = StreamlitKnowledgeBase(cache_path=os.path.join(self.tmp, "kb"))

    def test_search_chat_returns_results(self):
        results = self.kb.search_examples("chat")
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)

    def test_search_result_has_title_and_category(self):
        results = self.kb.search_examples("chart")
        for r in results:
            self.assertIn("title", r)
            self.assertIn("category", r)
            self.assertIn("type", r)

    def test_search_limit_respected(self):
        results = self.kb.search_examples("st", limit=2)
        self.assertLessEqual(len(results), 2)

    def test_search_nonsense_returns_empty(self):
        results = self.kb.search_examples("xyzzy_nonexistent_thing")
        self.assertEqual(len(results), 0)

    def test_search_input_finds_input_widgets(self):
        results = self.kb.search_examples("input")
        titles = [r["title"] for r in results]
        self.assertTrue(any("input" in t.lower() for t in titles))

    def test_search_by_category_name(self):
        results = self.kb.search_examples("navigation")
        self.assertGreater(len(results), 0)


class TestGetDeprecations(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.kb = StreamlitKnowledgeBase(cache_path=os.path.join(self.tmp, "kb"))

    def test_returns_list(self):
        deprecations = self.kb.get_deprecations()
        self.assertIsInstance(deprecations, list)

    def test_deprecation_has_feature_field(self):
        deprecations = self.kb.get_deprecations()
        for d in deprecations:
            self.assertIn("feature", d)
            self.assertIn("replacement", d)

    def test_st_cache_is_deprecated(self):
        deprecations = self.kb.get_deprecations()
        features = [d["feature"] for d in deprecations]
        self.assertIn("@st.cache", features)


class TestGetBestPractices(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.kb = StreamlitKnowledgeBase(cache_path=os.path.join(self.tmp, "kb"))

    def test_returns_list_of_strings(self):
        practices = self.kb.get_best_practices()
        self.assertIsInstance(practices, list)
        for p in practices:
            self.assertIsInstance(p, str)

    def test_includes_page_config_practice(self):
        practices = self.kb.get_best_practices()
        self.assertTrue(any("set_page_config" in p for p in practices))


class TestGetLatestFeatures(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.cache_path = os.path.join(self.tmp, "kb")
        self.kb = StreamlitKnowledgeBase(cache_path=self.cache_path)

    def test_returns_dict(self):
        features = self.kb.get_latest_features()
        self.assertIsInstance(features, dict)

    def test_has_version_key(self):
        features = self.kb.get_latest_features()
        self.assertIn("version", features)

    def test_returns_from_valid_cache(self):
        cache_file = Path(self.cache_path) / "features.json"
        cache_file.write_text(json.dumps({
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "data": {"version": "99.0.0", "features": {}, "deprecations": [], "best_practices": []},
        }))
        features = self.kb.get_latest_features()
        self.assertEqual(features["version"], "99.0.0")

    def test_fallback_to_builtin(self):
        features = self.kb.get_latest_features()
        self.assertIn("features", features)


class TestGetCurrentVersion(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.cache_path = os.path.join(self.tmp, "kb")
        self.kb = StreamlitKnowledgeBase(cache_path=self.cache_path)

    def test_returns_string(self):
        version = self.kb.get_current_version()
        self.assertIsInstance(version, str)

    def test_fallback_version_format(self):
        version = self.kb.get_current_version()
        parts = version.split(".")
        self.assertGreaterEqual(len(parts), 2)


if __name__ == "__main__":
    unittest.main()

"""Tests for AutoUpdatingKnowledgeBase — no mocks, real functional calls."""

import json
import os
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

from streamlitforge.knowledge.auto_update import AutoUpdatingKnowledgeBase, UPDATE_SCHEDULE


class TestAutoUpdatingInit(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.cache_path = os.path.join(self.tmp, "knowledge")

    def test_creates_cache_dir(self):
        kb = AutoUpdatingKnowledgeBase(cache_path=self.cache_path)
        self.assertTrue(Path(self.cache_path).is_dir())

    def test_default_update_interval(self):
        kb = AutoUpdatingKnowledgeBase(cache_path=self.cache_path)
        self.assertEqual(kb.update_interval, 24)

    def test_custom_update_interval(self):
        kb = AutoUpdatingKnowledgeBase(cache_path=self.cache_path, update_interval_hours=6)
        self.assertEqual(kb.update_interval, 6)

    def test_no_background_thread_by_default(self):
        kb = AutoUpdatingKnowledgeBase(cache_path=self.cache_path)
        self.assertIsNone(kb._updater_thread)


class TestSources(unittest.TestCase):
    def test_has_six_sources(self):
        self.assertEqual(len(AutoUpdatingKnowledgeBase.SOURCES), 6)

    def test_pypi_source_exists(self):
        self.assertIn("pypi", AutoUpdatingKnowledgeBase.SOURCES)

    def test_all_sources_have_required_keys(self):
        for name, config in AutoUpdatingKnowledgeBase.SOURCES.items():
            self.assertIn("url", config, f"Source {name} missing 'url'")
            self.assertIn("priority", config, f"Source {name} missing 'priority'")
            self.assertIn("cache_hours", config, f"Source {name} missing 'cache_hours'")


class TestUpdateSchedule(unittest.TestCase):
    def test_critical_has_version_info(self):
        self.assertIn("version_info", UPDATE_SCHEDULE["critical"])

    def test_important_has_new_features(self):
        self.assertIn("new_features", UPDATE_SCHEDULE["important"])

    def test_normal_has_examples(self):
        self.assertIn("examples", UPDATE_SCHEDULE["normal"])


class TestCacheValidity(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.cache_path = os.path.join(self.tmp, "knowledge")
        self.kb = AutoUpdatingKnowledgeBase(cache_path=self.cache_path)

    def test_nonexistent_is_invalid(self):
        fake = Path(self.cache_path) / "nonexistent.json"
        self.assertFalse(self.kb._is_cache_valid(fake, 24))

    def test_fresh_cache_is_valid(self):
        cache_file = Path(self.cache_path) / "test.json"
        cache_file.write_text(json.dumps({
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "data": {},
        }))
        self.assertTrue(self.kb._is_cache_valid(cache_file, 24))

    def test_stale_cache_is_invalid(self):
        cache_file = Path(self.cache_path) / "stale.json"
        old_time = datetime.now(timezone.utc) - timedelta(hours=48)
        cache_file.write_text(json.dumps({
            "fetched_at": old_time.isoformat(),
            "data": {},
        }))
        self.assertFalse(self.kb._is_cache_valid(cache_file, 24))

    def test_corrupt_json_is_invalid(self):
        cache_file = Path(self.cache_path) / "bad.json"
        cache_file.write_text("not json!")
        self.assertFalse(self.kb._is_cache_valid(cache_file, 24))

    def test_missing_fetched_at_is_invalid(self):
        cache_file = Path(self.cache_path) / "nots.json"
        cache_file.write_text(json.dumps({"data": {}}))
        self.assertFalse(self.kb._is_cache_valid(cache_file, 24))


class TestGetCachedData(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.cache_path = os.path.join(self.tmp, "knowledge")
        self.kb = AutoUpdatingKnowledgeBase(cache_path=self.cache_path)

    def test_returns_none_for_missing_source(self):
        result = self.kb.get_cached_data("nonexistent_source")
        self.assertIsNone(result)

    def test_returns_data_for_existing_cache(self):
        cache_file = Path(self.cache_path) / "test_source.json"
        cache_file.write_text(json.dumps({
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "data": {"key": "value"},
        }))
        result = self.kb.get_cached_data("test_source")
        self.assertEqual(result, {"key": "value"})

    def test_returns_none_for_corrupt_cache(self):
        cache_file = Path(self.cache_path) / "corrupt.json"
        cache_file.write_text("not json!")
        result = self.kb.get_cached_data("corrupt")
        self.assertIsNone(result)


class TestGetStatus(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.cache_path = os.path.join(self.tmp, "knowledge")
        self.kb = AutoUpdatingKnowledgeBase(cache_path=self.cache_path)

    def test_status_has_all_sources(self):
        status = self.kb.get_status()
        for source_name in AutoUpdatingKnowledgeBase.SOURCES:
            self.assertIn(source_name, status)

    def test_uncached_sources_show_not_cached(self):
        status = self.kb.get_status()
        for source_name, info in status.items():
            self.assertFalse(info["cached"])
            self.assertFalse(info["valid"])

    def test_cached_source_shows_cached(self):
        cache_file = Path(self.cache_path) / "pypi.json"
        cache_file.write_text(json.dumps({
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "data": {"version": "1.41.0"},
        }))
        status = self.kb.get_status()
        self.assertTrue(status["pypi"]["cached"])
        self.assertTrue(status["pypi"]["valid"])


class TestUpdateGeneric(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.cache_path = os.path.join(self.tmp, "knowledge")
        self.kb = AutoUpdatingKnowledgeBase(cache_path=self.cache_path)

    def test_generic_update_creates_cache_file(self):
        self.kb._update_generic("test_source", "https://example.com")
        cache_file = Path(self.cache_path) / "test_source.json"
        self.assertTrue(cache_file.exists())

    def test_generic_update_has_fetched_at(self):
        self.kb._update_generic("test_source", "https://example.com")
        cache_file = Path(self.cache_path) / "test_source.json"
        data = json.loads(cache_file.read_text())
        self.assertIn("fetched_at", data)

    def test_generic_update_has_source_url(self):
        self.kb._update_generic("test_source", "https://example.com")
        cache_file = Path(self.cache_path) / "test_source.json"
        data = json.loads(cache_file.read_text())
        self.assertEqual(data["source_url"], "https://example.com")


class TestGetCurrentVersion(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.cache_path = os.path.join(self.tmp, "knowledge")
        self.kb = AutoUpdatingKnowledgeBase(cache_path=self.cache_path)

    def test_returns_string(self):
        version = self.kb.get_current_version()
        self.assertIsInstance(version, str)

    def test_returns_cached_version_if_available(self):
        cache_file = Path(self.cache_path) / "pypi.json"
        cache_file.write_text(json.dumps({
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "data": {"version": "99.9.9"},
        }))
        version = self.kb.get_current_version()
        self.assertEqual(version, "99.9.9")

    def test_fallback_version(self):
        version = self.kb.get_current_version()
        parts = version.split(".")
        self.assertGreaterEqual(len(parts), 2)


class TestUpdateIfStale(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.cache_path = os.path.join(self.tmp, "knowledge")
        self.kb = AutoUpdatingKnowledgeBase(cache_path=self.cache_path)

    def test_fresh_cache_skips_update(self):
        for source_name in AutoUpdatingKnowledgeBase.SOURCES:
            cache_file = Path(self.cache_path) / f"{source_name}.json"
            cache_file.write_text(json.dumps({
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "data": {},
            }))
        results = self.kb.update_if_stale()
        for source_name in AutoUpdatingKnowledgeBase.SOURCES:
            self.assertTrue(results[source_name])

    def test_returns_dict_with_all_sources(self):
        results = self.kb.update_if_stale()
        for source_name in AutoUpdatingKnowledgeBase.SOURCES:
            self.assertIn(source_name, results)


class TestForceUpdate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.cache_path = os.path.join(self.tmp, "knowledge")
        self.kb = AutoUpdatingKnowledgeBase(cache_path=self.cache_path)

    def test_clears_cache_files(self):
        for source_name in AutoUpdatingKnowledgeBase.SOURCES:
            cache_file = Path(self.cache_path) / f"{source_name}.json"
            cache_file.write_text(json.dumps({
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "data": {"old": True},
            }))
        self.kb.force_update()
        for source_name in AutoUpdatingKnowledgeBase.SOURCES:
            cache_file = Path(self.cache_path) / f"{source_name}.json"
            if cache_file.exists():
                data = json.loads(cache_file.read_text())
                self.assertNotIn("old", data.get("data", {}))


class TestBackgroundUpdater(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.cache_path = os.path.join(self.tmp, "knowledge")

    def test_start_creates_thread(self):
        kb = AutoUpdatingKnowledgeBase(cache_path=self.cache_path)
        kb.start_background_updater()
        self.assertIsNotNone(kb._updater_thread)
        self.assertTrue(kb._updater_thread.daemon)

    def test_double_start_does_not_duplicate(self):
        kb = AutoUpdatingKnowledgeBase(cache_path=self.cache_path)
        kb.start_background_updater()
        thread1 = kb._updater_thread
        kb.start_background_updater()
        thread2 = kb._updater_thread
        self.assertIs(thread1, thread2)


if __name__ == "__main__":
    unittest.main()

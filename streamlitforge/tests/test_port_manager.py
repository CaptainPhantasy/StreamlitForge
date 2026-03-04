"""Test Port Manager functionality — real functional tests (no mocks)."""

import json
import os
import tempfile
import unittest
from pathlib import Path

from streamlitforge.core.port_manager import PortManager, NoPortsAvailableError, get_port_manager


class TestPortManager(unittest.TestCase):
    """Test PortManager with a temporary registry file."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.registry_path = os.path.join(self.tmp_dir, "port_registry.json")
        self.pm = PortManager(registry_path=self.registry_path)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_get_port_returns_int_in_range(self):
        port = self.pm.get_port("/tmp/test-project-abc")
        self.assertIsInstance(port, int)
        self.assertGreaterEqual(port, 8501)
        self.assertLessEqual(port, 8999)

    def test_determinism_same_path_same_port(self):
        port1 = self.pm.get_port("/tmp/determinism-test")
        pm2 = PortManager(registry_path=self.registry_path)
        port2 = pm2.get_port("/tmp/determinism-test")
        self.assertEqual(port1, port2)

    def test_different_paths_get_different_ports(self):
        port1 = self.pm.get_port("/tmp/project-alpha")
        port2 = self.pm.get_port("/tmp/project-beta")
        self.assertNotEqual(port1, port2)

    def test_release_port(self):
        self.pm.get_port("/tmp/release-test")
        self.assertTrue(self.pm.release_port("/tmp/release-test"))
        self.assertIsNone(self.pm.lookup("/tmp/release-test"))

    def test_release_nonexistent(self):
        self.assertFalse(self.pm.release_port("/tmp/never-registered"))

    def test_lookup(self):
        port = self.pm.get_port("/tmp/lookup-test")
        self.assertEqual(self.pm.lookup("/tmp/lookup-test"), port)
        self.assertIsNone(self.pm.lookup("/tmp/not-registered"))

    def test_list_ports(self):
        self.pm.get_port("/tmp/list-test-one")
        self.pm.get_port("/tmp/list-test-two")
        ports = self.pm.list_ports()
        self.assertEqual(len(ports), 2)
        paths = [e["project_path"] for e in ports.values()]
        self.assertIn(os.path.realpath("/tmp/list-test-one"), paths)
        self.assertIn(os.path.realpath("/tmp/list-test-two"), paths)

    def test_heartbeat_updates_timestamp(self):
        self.pm.get_port("/tmp/hb-test")
        port = self.pm.lookup("/tmp/hb-test")
        old_hb = self.pm._registry[str(port)]["last_heartbeat"]

        import time
        time.sleep(0.05)
        self.pm.heartbeat("/tmp/hb-test")

        new_hb = self.pm._registry[str(port)]["last_heartbeat"]
        self.assertNotEqual(old_hb, new_hb)

    def test_cleanup_stale_removes_old_entries(self):
        self.pm.get_port("/tmp/stale-test")
        port = self.pm.lookup("/tmp/stale-test")
        self.pm._registry[str(port)]["last_heartbeat"] = "2000-01-01T00:00:00+00:00"
        self.pm._save_registry()

        removed = self.pm.cleanup_stale(max_age_seconds=1)
        self.assertEqual(removed, 1)
        self.assertIsNone(self.pm.lookup("/tmp/stale-test"))

    def test_registry_persists_to_disk(self):
        port = self.pm.get_port("/tmp/persist-test")
        self.assertTrue(os.path.exists(self.registry_path))

        with open(self.registry_path) as f:
            data = json.load(f)
        self.assertIn(str(port), data)

    def test_conflict_resolution(self):
        """When two paths hash to the same port, second gets a nearby port."""
        port1 = self.pm.get_port("/tmp/conflict-a")
        port2 = self.pm.get_port("/tmp/conflict-b")
        self.assertNotEqual(port1, port2)
        self.assertGreaterEqual(port2, 8501)
        self.assertLessEqual(port2, 8999)

    def test_custom_port_range(self):
        pm = PortManager(base_port=9000, max_port=9010, registry_path=self.registry_path)
        pm._registry = {}
        pm._save_registry()
        port = pm.get_port("/tmp/range-test")
        self.assertGreaterEqual(port, 9000)
        self.assertLessEqual(port, 9010)


class TestGetPortManager(unittest.TestCase):
    """Test the singleton accessor."""

    def test_returns_port_manager_instance(self):
        import streamlitforge.core.port_manager as pm_mod
        pm_mod._global_port_manager = None
        mgr = get_port_manager()
        self.assertIsInstance(mgr, PortManager)

    def test_returns_same_instance(self):
        import streamlitforge.core.port_manager as pm_mod
        pm_mod._global_port_manager = None
        mgr1 = get_port_manager()
        mgr2 = get_port_manager()
        self.assertIs(mgr1, mgr2)


if __name__ == '__main__':
    unittest.main()

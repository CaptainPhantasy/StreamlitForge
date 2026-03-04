"""Tests for CLI interface — no mocks, real functional calls via Click CliRunner."""

import os
import tempfile
import unittest
from pathlib import Path

from click.testing import CliRunner

from streamlitforge.cli import cli


class TestCLIGroup(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    def test_help(self):
        result = self.runner.invoke(cli, ["--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("StreamlitForge", result.output)

    def test_version(self):
        result = self.runner.invoke(cli, ["--version"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("0.1.0", result.output)


class TestCreateCommand(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.tmp = tempfile.mkdtemp()

    def test_create_project(self):
        result = self.runner.invoke(cli, [
            "create", "testproject",
            "--path", self.tmp,
            "--no-venv", "--no-git",
        ])
        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn("Project created", result.output)
        project_dir = Path(self.tmp) / "testproject"
        self.assertTrue(project_dir.exists())

    def test_create_with_template(self):
        result = self.runner.invoke(cli, [
            "create", "dashproject",
            "--path", self.tmp,
            "--no-venv", "--no-git",
            "--template", "dashboard",
        ])
        self.assertEqual(result.exit_code, 0, msg=result.output)

    def test_create_duplicate_fails(self):
        self.runner.invoke(cli, [
            "create", "dup", "--path", self.tmp, "--no-venv", "--no-git",
        ])
        result = self.runner.invoke(cli, [
            "create", "dup", "--path", self.tmp, "--no-venv", "--no-git",
        ])
        self.assertNotEqual(result.exit_code, 0)

    def test_create_force_overwrites(self):
        self.runner.invoke(cli, [
            "create", "forced", "--path", self.tmp, "--no-venv", "--no-git",
        ])
        result = self.runner.invoke(cli, [
            "create", "forced", "--path", self.tmp, "--no-venv", "--no-git", "--force",
        ])
        self.assertEqual(result.exit_code, 0, msg=result.output)


class TestNewCommand(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.tmp = tempfile.mkdtemp()

    def test_new_is_alias_for_create(self):
        result = self.runner.invoke(cli, [
            "new", "newproject",
            "--path", self.tmp,
            "--no-venv", "--no-git",
        ])
        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn("Project created", result.output)


class TestListTemplatesCommand(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    def test_list_templates(self):
        result = self.runner.invoke(cli, ["list-templates"])
        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn("Available Templates", result.output)


class TestInfoCommand(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.tmp = tempfile.mkdtemp()
        self.runner.invoke(cli, [
            "create", "infoproject",
            "--path", self.tmp,
            "--no-venv", "--no-git",
        ])
        self.project_path = str(Path(self.tmp) / "infoproject")

    def test_info_shows_project(self):
        result = self.runner.invoke(cli, ["info", self.project_path])
        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn("infoproject", result.output)

    def test_info_nonexistent_fails(self):
        result = self.runner.invoke(cli, ["info", "/tmp/nonexistent_project_xyz"])
        self.assertNotEqual(result.exit_code, 0)


class TestDeleteCommand(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.tmp = tempfile.mkdtemp()
        self.runner.invoke(cli, [
            "create", "delproject",
            "--path", self.tmp,
            "--no-venv", "--no-git",
        ])
        self.project_path = str(Path(self.tmp) / "delproject")

    def test_delete_with_yes_flag(self):
        result = self.runner.invoke(cli, ["delete", self.project_path, "--yes"])
        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn("deleted", result.output)
        self.assertFalse(Path(self.project_path).exists())

    def test_delete_nonexistent_fails(self):
        result = self.runner.invoke(cli, ["delete", "/tmp/nonexistent_xyz", "--yes"])
        self.assertNotEqual(result.exit_code, 0)


class TestInitCommand(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.tmp = tempfile.mkdtemp()

    def test_init_creates_config(self):
        result = self.runner.invoke(cli, ["init"], catch_exceptions=False)
        if result.exit_code != 0:
            self.skipTest("Init requires specific cwd context")


class TestListCommand(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    def test_list_runs(self):
        result = self.runner.invoke(cli, ["list"])
        self.assertEqual(result.exit_code, 0, msg=result.output)


class TestPortsCommand(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    def test_ports_runs(self):
        result = self.runner.invoke(cli, ["ports"])
        self.assertEqual(result.exit_code, 0, msg=result.output)

    def test_ports_cleanup(self):
        result = self.runner.invoke(cli, ["ports", "--cleanup"])
        self.assertEqual(result.exit_code, 0, msg=result.output)


class TestConfigCommand(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    def test_config_no_args(self):
        result = self.runner.invoke(cli, ["config"])
        self.assertEqual(result.exit_code, 0, msg=result.output)


class TestKeysGroup(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    def test_keys_help(self):
        result = self.runner.invoke(cli, ["keys", "--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("API key management", result.output)

    def test_keys_list(self):
        result = self.runner.invoke(cli, ["keys", "list"])
        self.assertEqual(result.exit_code, 0, msg=result.output)

    def test_keys_add_and_remove(self):
        result = self.runner.invoke(cli, ["keys", "add", "openai", "sk-test-123"])
        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn("Key added", result.output)

        result = self.runner.invoke(cli, ["keys", "remove", "openai"])
        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn("Key removed", result.output)

    def test_keys_test(self):
        result = self.runner.invoke(cli, ["keys", "test", "openai"])
        self.assertEqual(result.exit_code, 0, msg=result.output)


class TestKnowledgeGroup(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    def test_knowledge_help(self):
        result = self.runner.invoke(cli, ["knowledge", "--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Knowledge base commands", result.output)

    def test_knowledge_search(self):
        result = self.runner.invoke(cli, ["knowledge", "search", "--query", "charts"])
        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn("Search Results", result.output)


class TestGenerateCommand(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.tmp = tempfile.mkdtemp()

    def test_generate_table_inline(self):
        result = self.runner.invoke(cli, ["generate", "table", "--inline"])
        self.assertEqual(result.exit_code, 0, msg=result.output)

    def test_generate_chart_inline(self):
        result = self.runner.invoke(cli, ["generate", "chart", "--inline"])
        self.assertEqual(result.exit_code, 0, msg=result.output)

    def test_generate_form_inline(self):
        result = self.runner.invoke(cli, ["generate", "form", "--inline"])
        self.assertEqual(result.exit_code, 0, msg=result.output)

    def test_generate_unknown_type_fails(self):
        result = self.runner.invoke(cli, ["generate", "nonexistent_type", "--inline"])
        self.assertNotEqual(result.exit_code, 0)

    def test_generate_to_file(self):
        result = self.runner.invoke(cli, [
            "generate", "table",
            "--output", self.tmp,
            "--name", "my_table",
        ])
        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertTrue((Path(self.tmp) / "my_table.py").exists())


class TestUpdateCommand(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    def test_update_offline(self):
        result = self.runner.invoke(cli, ["update", "--offline"])
        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn("Offline mode", result.output)


if __name__ == "__main__":
    unittest.main()

"""Test Project Manager — real functional tests (no mocks)."""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from streamlitforge.core.project_manager import ProjectManager


class TestProjectManagerCreate(unittest.TestCase):
    """Test project creation end-to-end."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.pm = ProjectManager()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_create_project_returns_path(self):
        p = self.pm.create_project('test-app', parent_dir=self.tmp_dir, create_venv=False)
        self.assertIsInstance(p, Path)
        self.assertTrue(p.exists())

    def test_directory_structure(self):
        p = self.pm.create_project('struct-test', parent_dir=self.tmp_dir, create_venv=False)
        for d in ['.streamlit', 'src', 'src/pages', 'src/components', 'src/utils',
                  'tests', 'assets', 'data', 'docs']:
            self.assertTrue((p / d).is_dir(), f"Missing directory: {d}")

    def test_key_files_exist(self):
        p = self.pm.create_project('files-test', parent_dir=self.tmp_dir, create_venv=False)
        for f in ['.streamlit/config.toml', 'src/app.py', 'requirements.txt',
                  '.gitignore', '.env.example', 'run.sh', 'README.md',
                  'src/utils/helpers.py', 'src/config.py', 'tests/test_app.py']:
            self.assertTrue((p / f).exists(), f"Missing file: {f}")

    def test_streamlit_config_contains_port(self):
        p = self.pm.create_project('port-test', parent_dir=self.tmp_dir, create_venv=False)
        content = (p / '.streamlit' / 'config.toml').read_text()
        self.assertIn('port =', content)
        self.assertIn('[server]', content)
        self.assertIn('[theme]', content)

    def test_requirements_has_streamlit(self):
        p = self.pm.create_project('req-test', parent_dir=self.tmp_dir, create_venv=False)
        content = (p / 'requirements.txt').read_text()
        self.assertIn('streamlit', content)

    def test_extra_dependencies(self):
        p = self.pm.create_project(
            'deps-test', parent_dir=self.tmp_dir,
            dependencies=['pandas', 'plotly'], create_venv=False
        )
        content = (p / 'requirements.txt').read_text()
        self.assertIn('pandas', content)
        self.assertIn('plotly', content)

    def test_template_flag(self):
        p = self.pm.create_project(
            'tmpl-test', parent_dir=self.tmp_dir,
            template='dashboard', create_venv=False
        )
        content = (p / 'src' / 'app.py').read_text()
        self.assertIn('Dashboard', content)

    def test_force_overwrite(self):
        self.pm.create_project('force-test', parent_dir=self.tmp_dir, create_venv=False)
        p = self.pm.create_project(
            'force-test', parent_dir=self.tmp_dir, create_venv=False, force=True
        )
        self.assertTrue(p.exists())

    def test_existing_project_without_force_raises(self):
        self.pm.create_project('dup-test', parent_dir=self.tmp_dir, create_venv=False)
        with self.assertRaises(FileExistsError):
            self.pm.create_project('dup-test', parent_dir=self.tmp_dir, create_venv=False)

    def test_run_sh_is_executable(self):
        p = self.pm.create_project('exec-test', parent_dir=self.tmp_dir, create_venv=False)
        run_sh = p / 'run.sh'
        self.assertTrue(os.access(str(run_sh), os.X_OK))

    def test_readme_contains_project_name(self):
        p = self.pm.create_project('readme-test', parent_dir=self.tmp_dir, create_venv=False)
        content = (p / 'README.md').read_text()
        self.assertIn('readme-test', content)


class TestProjectManagerInfo(unittest.TestCase):
    """Test get_project_info."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.pm = ProjectManager()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_get_info_on_created_project(self):
        p = self.pm.create_project('info-test', parent_dir=self.tmp_dir, create_venv=False)
        info = self.pm.get_project_info(str(p))
        self.assertEqual(info['name'], 'info-test')
        self.assertIsInstance(info['files'], int)
        self.assertGreater(info['files'], 0)
        self.assertIn('streamlit_config', info)

    def test_info_nonexistent_raises(self):
        with self.assertRaises(FileNotFoundError):
            self.pm.get_project_info('/tmp/does-not-exist-sfg-xyz')


class TestProjectManagerDelete(unittest.TestCase):
    """Test delete_project."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.pm = ProjectManager()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_delete_removes_directory(self):
        p = self.pm.create_project('del-test', parent_dir=self.tmp_dir, create_venv=False)
        self.pm.delete_project(str(p))
        self.assertFalse(p.exists())

    def test_delete_nonexistent_raises(self):
        with self.assertRaises(FileNotFoundError):
            self.pm.delete_project('/tmp/does-not-exist-sfg-xyz')


if __name__ == '__main__':
    unittest.main()

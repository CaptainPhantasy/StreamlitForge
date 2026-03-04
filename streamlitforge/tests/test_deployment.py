"""Tests for Deployment & Sharing — no mocks, real functional calls."""

import os
import tempfile
import unittest
from pathlib import Path

from streamlitforge.deployment import (
    DeploymentConfigGenerator,
    DeploymentManager,
    DeploymentResult,
    ProjectInfo,
    SharingManager,
)


class TestProjectInfo(unittest.TestCase):
    def test_defaults(self):
        p = ProjectInfo(name="myapp", path="/tmp/myapp")
        self.assertEqual(p.name, "myapp")
        self.assertEqual(p.path, "/tmp/myapp")
        self.assertEqual(p.port, 8501)
        self.assertEqual(p.python_version, "3.11")

    def test_custom_port(self):
        p = ProjectInfo(name="app", path="/tmp/app", port=9000)
        self.assertEqual(p.port, 9000)


class TestDeploymentResult(unittest.TestCase):
    def test_success_result(self):
        r = DeploymentResult(success=True, platform="docker", message="Done")
        self.assertTrue(r.success)
        self.assertEqual(r.platform, "docker")
        self.assertEqual(r.message, "Done")
        self.assertEqual(r.files_created, [])

    def test_failure_result(self):
        r = DeploymentResult(success=False, platform="k8s", message="Not supported")
        self.assertFalse(r.success)


class TestDeploymentConfigGenerator(unittest.TestCase):
    def setUp(self):
        self.gen = DeploymentConfigGenerator()
        self.project = ProjectInfo(name="testapp", path="/tmp/testapp", port=8501)

    def test_dockerfile_has_from(self):
        df = self.gen.generate_dockerfile(self.project)
        self.assertIn("FROM python:3.11-slim", df)

    def test_dockerfile_has_port(self):
        df = self.gen.generate_dockerfile(self.project)
        self.assertIn("EXPOSE 8501", df)

    def test_dockerfile_has_healthcheck(self):
        df = self.gen.generate_dockerfile(self.project)
        self.assertIn("HEALTHCHECK", df)

    def test_dockerfile_has_cmd(self):
        df = self.gen.generate_dockerfile(self.project)
        self.assertIn("CMD", df)
        self.assertIn("streamlit", df)

    def test_dockerfile_custom_port(self):
        project = ProjectInfo(name="app", path="/tmp", port=9000)
        df = self.gen.generate_dockerfile(project)
        self.assertIn("EXPOSE 9000", df)
        self.assertIn("9000", df)

    def test_docker_compose_has_version(self):
        dc = self.gen.generate_docker_compose(self.project)
        self.assertIn("version:", dc)

    def test_docker_compose_has_service(self):
        dc = self.gen.generate_docker_compose(self.project)
        self.assertIn("services:", dc)
        self.assertIn("app:", dc)

    def test_docker_compose_port_mapping(self):
        dc = self.gen.generate_docker_compose(self.project)
        self.assertIn("8501:8501", dc)

    def test_render_yaml_has_service_type(self):
        ry = self.gen.generate_render_yaml(self.project)
        self.assertIn("type: web", ry)
        self.assertIn("name: testapp", ry)

    def test_render_yaml_has_build_command(self):
        ry = self.gen.generate_render_yaml(self.project)
        self.assertIn("buildCommand:", ry)
        self.assertIn("pip install", ry)

    def test_procfile_has_web(self):
        pf = self.gen.generate_procfile(self.project)
        self.assertTrue(pf.startswith("web:"))
        self.assertIn("streamlit run", pf)

    def test_railway_toml_has_deploy(self):
        rt = self.gen.generate_railway_toml(self.project)
        self.assertIn("[deploy]", rt)
        self.assertIn("streamlit run", rt)

    def test_railway_toml_has_build(self):
        rt = self.gen.generate_railway_toml(self.project)
        self.assertIn("[build]", rt)
        self.assertIn("nixpacks", rt)


class TestDeploymentManager(unittest.TestCase):
    def setUp(self):
        self.mgr = DeploymentManager()
        self.tmp = tempfile.mkdtemp()
        self.project = ProjectInfo(name="testapp", path=self.tmp, port=8501)

    def test_has_nine_platforms(self):
        self.assertEqual(len(self.mgr.PLATFORMS), 9)

    def test_list_platforms(self):
        platforms = self.mgr.list_platforms()
        self.assertEqual(len(platforms), 9)
        ids = [p["id"] for p in platforms]
        self.assertIn("docker", ids)
        self.assertIn("streamlit_cloud", ids)
        self.assertIn("render", ids)

    def test_list_platforms_has_free_tier_info(self):
        platforms = self.mgr.list_platforms()
        for p in platforms:
            self.assertIn("free_tier", p)
            self.assertIn("name", p)

    def test_generate_docker_config(self):
        result = self.mgr.generate_config(self.project, "docker")
        self.assertTrue(result.success)
        self.assertEqual(result.platform, "docker")
        self.assertEqual(len(result.files_created), 2)
        self.assertTrue((Path(self.tmp) / "Dockerfile").exists())
        self.assertTrue((Path(self.tmp) / "docker-compose.yml").exists())

    def test_docker_dockerfile_content(self):
        self.mgr.generate_config(self.project, "docker")
        content = (Path(self.tmp) / "Dockerfile").read_text()
        self.assertIn("FROM python", content)

    def test_generate_render_config(self):
        result = self.mgr.generate_config(self.project, "render")
        self.assertTrue(result.success)
        self.assertEqual(len(result.files_created), 1)
        self.assertTrue((Path(self.tmp) / "render.yaml").exists())

    def test_generate_heroku_config(self):
        result = self.mgr.generate_config(self.project, "heroku")
        self.assertTrue(result.success)
        self.assertTrue((Path(self.tmp) / "Procfile").exists())

    def test_generate_railway_config(self):
        result = self.mgr.generate_config(self.project, "railway")
        self.assertTrue(result.success)
        self.assertTrue((Path(self.tmp) / "railway.toml").exists())

    def test_unsupported_platform_returns_failure(self):
        result = self.mgr.generate_config(self.project, "streamlit_cloud")
        self.assertFalse(result.success)
        self.assertIn("not yet implemented", result.message)

    def test_result_message_includes_platform_name(self):
        result = self.mgr.generate_config(self.project, "docker")
        self.assertIn("Docker", result.message)


class TestSharingManager(unittest.TestCase):
    def setUp(self):
        self.sharing = SharingManager()

    def test_embed_code_returns_iframe(self):
        code = self.sharing.embed_code("https://myapp.streamlit.app")
        self.assertIn("<iframe", code)
        self.assertIn("</iframe>", code)

    def test_embed_code_includes_url(self):
        code = self.sharing.embed_code("https://myapp.streamlit.app")
        self.assertIn("https://myapp.streamlit.app?embed=true", code)

    def test_embed_code_default_height(self):
        code = self.sharing.embed_code("https://myapp.streamlit.app")
        self.assertIn('height="800"', code)

    def test_embed_code_custom_height(self):
        code = self.sharing.embed_code("https://myapp.streamlit.app", height=600)
        self.assertIn('height="600"', code)

    def test_embed_code_has_no_border(self):
        code = self.sharing.embed_code("https://myapp.streamlit.app")
        self.assertIn("border: none", code)


if __name__ == "__main__":
    unittest.main()

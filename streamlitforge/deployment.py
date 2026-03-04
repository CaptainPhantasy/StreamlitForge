"""Deployment & Sharing Integration."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ProjectInfo:
    name: str
    path: str
    port: int = 8501
    python_version: str = "3.11"


@dataclass
class DeploymentResult:
    success: bool
    platform: str
    url: Optional[str] = None
    repo_url: Optional[str] = None
    message: str = ""
    files_created: List[str] = field(default_factory=list)


class DeploymentConfigGenerator:
    """Generate deployment configs for various platforms."""

    def generate_dockerfile(self, project: ProjectInfo) -> str:
        return f"""FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE {project.port}

HEALTHCHECK CMD curl --fail http://localhost:{project.port}/_stcore/health

CMD ["streamlit", "run", "src/app.py", "--server.port={project.port}", "--server.address=0.0.0.0"]
"""

    def generate_docker_compose(self, project: ProjectInfo) -> str:
        return f"""version: '3.8'

services:
  app:
    build: .
    ports:
      - "{project.port}:{project.port}"
    environment:
      - STREAMLIT_SERVER_PORT={project.port}
    volumes:
      - ./data:/app/data
    restart: unless-stopped
"""

    def generate_render_yaml(self, project: ProjectInfo) -> str:
        return f"""services:
  - type: web
    name: {project.name}
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: streamlit run src/app.py --server.port=$PORT --server.address=0.0.0.0
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
"""

    def generate_procfile(self, project: ProjectInfo) -> str:
        return f"web: streamlit run src/app.py --server.port=$PORT --server.address=0.0.0.0\n"

    def generate_railway_toml(self, project: ProjectInfo) -> str:
        return f"""[build]
builder = "nixpacks"

[deploy]
startCommand = "streamlit run src/app.py --server.port=$PORT --server.address=0.0.0.0"
"""


class DeploymentManager:
    """Deploy Streamlit apps to various platforms."""

    PLATFORMS = {
        "streamlit_cloud": {"name": "Streamlit Community Cloud", "free_tier": True},
        "docker": {"name": "Docker Container", "free_tier": True},
        "kubernetes": {"name": "Kubernetes Cluster", "free_tier": False},
        "aws": {"name": "AWS (ECS/Fargate)", "free_tier": False},
        "gcp": {"name": "Google Cloud Run", "free_tier": True},
        "azure": {"name": "Azure Container Instances", "free_tier": False},
        "heroku": {"name": "Heroku", "free_tier": False},
        "render": {"name": "Render", "free_tier": True},
        "railway": {"name": "Railway", "free_tier": True},
    }

    def __init__(self):
        self.config_gen = DeploymentConfigGenerator()

    def list_platforms(self) -> List[Dict[str, Any]]:
        return [
            {"id": k, **v}
            for k, v in self.PLATFORMS.items()
        ]

    def generate_config(self, project: ProjectInfo, platform: str) -> DeploymentResult:
        from pathlib import Path
        project_path = Path(project.path)
        files_created: List[str] = []

        if platform == "docker":
            dockerfile = project_path / "Dockerfile"
            dockerfile.write_text(self.config_gen.generate_dockerfile(project))
            files_created.append(str(dockerfile))

            compose_file = project_path / "docker-compose.yml"
            compose_file.write_text(self.config_gen.generate_docker_compose(project))
            files_created.append(str(compose_file))

        elif platform == "render":
            render_file = project_path / "render.yaml"
            render_file.write_text(self.config_gen.generate_render_yaml(project))
            files_created.append(str(render_file))

        elif platform == "heroku":
            procfile = project_path / "Procfile"
            procfile.write_text(self.config_gen.generate_procfile(project))
            files_created.append(str(procfile))

        elif platform == "railway":
            railway_file = project_path / "railway.toml"
            railway_file.write_text(self.config_gen.generate_railway_toml(project))
            files_created.append(str(railway_file))

        else:
            return DeploymentResult(
                success=False,
                platform=platform,
                message=f"Platform '{platform}' config generation not yet implemented. Use Docker as a universal fallback.",
            )

        return DeploymentResult(
            success=True,
            platform=platform,
            files_created=files_created,
            message=f"Deployment config generated for {self.PLATFORMS.get(platform, {}).get('name', platform)}",
        )


class SharingManager:
    """Share Streamlit apps via various channels."""

    def embed_code(self, app_url: str, height: int = 800) -> str:
        return f'''<iframe
    src="{app_url}?embed=true"
    width="100%"
    height="{height}"
    style="border: none;">
</iframe>'''

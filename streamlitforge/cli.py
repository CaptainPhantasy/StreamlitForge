"""CLI interface for StreamlitForge — complete per PLANNING.md."""

import subprocess
import sys
from pathlib import Path
from typing import Optional

import click

from streamlitforge.core import Config, ConfigError, get_port_manager
from streamlitforge.core.project_manager import ProjectManager
from streamlitforge.knowledge import BuiltInKnowledgeBase
from streamlitforge.templates import BuiltInTemplates


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """StreamlitForge — AI-Powered Streamlit Application Builder CLI."""
    pass


# ---------------------------------------------------------------------------
# create / new
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("project_name")
@click.option("--path", "-p", help="Parent directory for the project", default=None)
@click.option("--dependencies", "-d", multiple=True, help="Additional dependencies")
@click.option("--template", "-t", help="Template (dashboard, chat, crud, analysis, admin)")
@click.option("--no-venv", is_flag=True, help="Skip virtual environment creation")
@click.option("--no-git", is_flag=True, help="Skip git initialization")
@click.option("--description", help="Project description")
@click.option("--force", "-f", is_flag=True, help="Force overwrite existing project")
def create(project_name, path, dependencies, template, no_venv, no_git, description, force):
    """Create a new Streamlit project."""
    _create_project(project_name, path, dependencies, template, no_venv, no_git, description, force)


@cli.command("new")
@click.argument("project_name")
@click.option("--path", "-p", help="Parent directory for the project", default=None)
@click.option("--dependencies", "-d", multiple=True, help="Additional dependencies")
@click.option("--template", "-t", help="Template (dashboard, chat, crud, analysis, admin)")
@click.option("--no-venv", is_flag=True, help="Skip virtual environment creation")
@click.option("--no-git", is_flag=True, help="Skip git initialization")
@click.option("--description", help="Project description")
@click.option("--force", "-f", is_flag=True, help="Force overwrite existing project")
def new(project_name, path, dependencies, template, no_venv, no_git, description, force):
    """Create a new Streamlit project (alias for create)."""
    _create_project(project_name, path, dependencies, template, no_venv, no_git, description, force)


def _create_project(project_name, path, dependencies, template, no_venv, no_git, description, force):
    try:
        pm = ProjectManager()
        project_dir = pm.create_project(
            project_name=project_name,
            parent_dir=path,
            template=template,
            dependencies=list(dependencies) if dependencies else None,
            create_venv=not no_venv,
            force=force,
        )

        if description:
            readme = project_dir / "README.md"
            if readme.exists():
                content = readme.read_text()
                content = content.replace(
                    "A Streamlit application.",
                    description,
                )
                readme.write_text(content)

        if not no_git:
            try:
                subprocess.run(
                    ["git", "init"],
                    cwd=str(project_dir),
                    capture_output=True,
                    timeout=10,
                )
                gitignore = project_dir / ".gitignore"
                if not gitignore.exists():
                    gitignore.write_text(
                        ".venv/\n__pycache__/\n*.pyc\n.env\n"
                        "secrets.toml\n.streamlit/secrets.toml\n"
                    )
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass

        port_mgr = get_port_manager()
        port = port_mgr.lookup(str(project_dir.resolve()))

        click.secho(f"  Project created at: {project_dir}", fg="green")
        click.echo()
        click.secho("Next steps:", fg="blue")
        click.echo(f"  1. cd {project_dir}")
        if not no_venv:
            click.echo("  2. source .venv/bin/activate")
        step = 3 if not no_venv else 2
        click.echo(f"  {step}. pip install -r requirements.txt")
        click.echo(f"  {step + 1}. streamlit run src/app.py --server.port {port or 8501}")

    except Exception as e:
        click.secho(f"  Error creating project: {e}", fg="red")
        sys.exit(1)


# ---------------------------------------------------------------------------
# list-templates
# ---------------------------------------------------------------------------

@cli.command("list-templates")
def list_templates():
    """List available templates."""
    try:
        templates = BuiltInTemplates.get_template_names()
        click.secho("Available Templates:", fg="cyan")
        click.echo()
        for i, t in enumerate(templates, 1):
            click.echo(f"  {i}. {t}")
        click.echo()
        click.echo("Use --template flag with create command to use a template.")
    except Exception as e:
        click.secho(f"  Error: {e}", fg="red")
        sys.exit(1)


# ---------------------------------------------------------------------------
# info
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("project_path")
def info(project_path):
    """Get information about a project."""
    try:
        pm = ProjectManager()
        project_info = pm.get_project_info(project_path)
        click.secho(f"Project: {project_info['name']}", fg="cyan")
        click.secho(f"Path:    {project_info['path']}", fg="cyan")
        click.secho(f"Port:    {project_info.get('port', 'not assigned')}", fg="cyan")
        click.secho(f"Files:   {project_info['files']}", fg="cyan")
        if project_info.get("streamlit_config"):
            click.echo()
            click.secho("Streamlit Config:", fg="cyan")
            click.echo(project_info["streamlit_config"])
    except FileNotFoundError:
        click.secho(f"  Project not found: {project_path}", fg="red")
        sys.exit(1)
    except Exception as e:
        click.secho(f"  Error: {e}", fg="red")
        sys.exit(1)


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("project_path")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
def delete(project_path, yes):
    """Delete a project."""
    try:
        p = Path(project_path).resolve()
        if not p.exists():
            click.secho(f"  Project not found: {project_path}", fg="red")
            sys.exit(1)
        if not yes and not click.confirm(f"Delete project at {p}?", default=False):
            click.secho("Cancelled", fg="yellow")
            return
        pm = ProjectManager()
        pm.delete_project(str(p))
        click.secho(f"  Project deleted: {p}", fg="green")
    except Exception as e:
        click.secho(f"  Error: {e}", fg="red")
        sys.exit(1)


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------

@cli.command()
def init():
    """Initialize StreamlitForge configuration in the current directory."""
    try:
        config_path = Path.cwd() / "streamlitforge_config.yaml"
        if config_path.exists():
            click.secho(f"  Configuration already exists at: {config_path}", fg="red")
            sys.exit(1)
        config = Config()
        config.load_from_dict({"project_name": Path.cwd().name, "port": 8501})
        config.save_to_file(str(config_path), format="yaml")
        click.secho(f"  Configuration created at: {config_path}", fg="green")
    except Exception as e:
        click.secho(f"  Error creating configuration: {e}", fg="red")
        sys.exit(1)


# ---------------------------------------------------------------------------
# list (projects)
# ---------------------------------------------------------------------------

@cli.command("list")
@click.option("--running", is_flag=True, help="Show only running projects")
@click.option("--all", "show_all", is_flag=True, help="Show all known projects")
def list_projects(running, show_all):
    """List known projects and their ports."""
    try:
        port_mgr = get_port_manager()
        entries = port_mgr.list_ports()
        if not entries:
            click.echo("No projects registered.")
            return
        click.secho(f"{'Project':<40} {'Port':<8} {'Status'}", fg="cyan")
        click.secho("-" * 60, fg="cyan")
        for port_str, entry in entries.items():
            path = entry.get("project_path", "unknown")
            name = entry.get("project_name", Path(path).name if path != "unknown" else "unknown")
            status = "active" if entry.get("active", False) else "idle"
            if running and status != "active":
                continue
            click.echo(f"  {name:<38} {port_str:<8} {status}")
    except Exception as e:
        click.secho(f"  Error: {e}", fg="red")
        sys.exit(1)


# ---------------------------------------------------------------------------
# ports
# ---------------------------------------------------------------------------

@cli.command()
@click.option("--cleanup", is_flag=True, help="Remove stale port assignments")
@click.option("--release", type=int, help="Release specific port")
@click.option("--show", type=str, help="Show port for project")
def ports(cleanup, release, show):
    """Manage port assignments."""
    try:
        port_mgr = get_port_manager()
        if cleanup:
            port_mgr.cleanup_stale()
            click.secho("  Stale ports cleaned up.", fg="green")
        elif release:
            port_mgr.release(str(release))
            click.secho(f"  Port {release} released.", fg="green")
        elif show:
            p = Path(show).resolve()
            port = port_mgr.lookup(str(p))
            if port:
                click.echo(f"  Port for {p.name}: {port}")
            else:
                click.echo(f"  No port assigned for {show}")
        else:
            entries = port_mgr.list_ports()
            if not entries:
                click.echo("  No ports assigned.")
                return
            click.secho(f"{'Port':<8} {'Project'}", fg="cyan")
            click.secho("-" * 50, fg="cyan")
            for port_str, entry in entries.items():
                path = entry.get("project_path", "unknown")
                name = entry.get("project_name", Path(path).name if path != "unknown" else "unknown")
                click.echo(f"  {port_str:<8} {name}")
    except Exception as e:
        click.secho(f"  Error: {e}", fg="red")
        sys.exit(1)


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("project_path")
@click.option("--port", type=int, help="Override port")
@click.option("--detach", "-d", is_flag=True, help="Run in background")
def run(project_path, port, detach):
    """Run a Streamlit project."""
    try:
        p = Path(project_path).resolve()
        if not p.exists():
            click.secho(f"  Project not found: {project_path}", fg="red")
            sys.exit(1)

        app_file = p / "src" / "app.py"
        if not app_file.exists():
            app_file = p / "app.py"
        if not app_file.exists():
            click.secho("  No app.py found in project", fg="red")
            sys.exit(1)

        if not port:
            port_mgr = get_port_manager()
            port = port_mgr.lookup(str(p)) or 8501

        cmd = [
            sys.executable, "-m", "streamlit", "run",
            str(app_file),
            f"--server.port={port}",
        ]

        click.secho(f"  Running {p.name} on port {port}...", fg="green")

        if detach:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            click.echo(f"  App started in background at http://localhost:{port}")
        else:
            subprocess.run(cmd)

    except Exception as e:
        click.secho(f"  Error: {e}", fg="red")
        sys.exit(1)


# ---------------------------------------------------------------------------
# generate
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("component_type")
@click.option("--name", "-n", help="Component name")
@click.option("--output", "-o", help="Output directory")
@click.option("--inline", is_flag=True, help="Print to stdout instead of file")
def generate(component_type, name, output, inline):
    """Generate a Streamlit component from a template."""
    try:
        from jinja2 import Environment, PackageLoader, select_autoescape

        component_name = name or component_type
        template_map = {
            "table": "components/table.py.j2",
            "chart": "components/chart.py.j2",
            "form": "components/form.py.j2",
        }

        template_file = template_map.get(component_type)
        if not template_file:
            click.secho(f"  Unknown component type: {component_type}", fg="red")
            click.echo(f"  Available: {', '.join(template_map.keys())}")
            sys.exit(1)

        env = Environment(
            loader=PackageLoader("streamlitforge", "templates"),
            autoescape=select_autoescape(),
        )
        template = env.get_template(template_file)

        context = {
            "component_name": component_name,
            "title": component_name.replace("_", " ").title(),
            "enable_search": True,
            "enable_export": True,
            "enable_pagination": False,
            "chart_type": "line",
            "show_data": True,
            "fields": [],
            "submit_label": "Submit",
        }
        rendered = template.render(**context)

        if inline:
            click.echo(rendered)
        else:
            output_dir = Path(output) if output else Path.cwd()
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"{component_name}.py"
            output_file.write_text(rendered)
            click.secho(f"  Component generated: {output_file}", fg="green")

    except Exception as e:
        click.secho(f"  Error: {e}", fg="red")
        sys.exit(1)


# ---------------------------------------------------------------------------
# add
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("project_path")
@click.argument("component_type")
@click.option("--page", is_flag=True, help="Add as a new page (multi-page app)")
@click.option("--component", is_flag=True, help="Add as reusable component")
@click.option("--name", "-n", help="Component name")
def add(project_path, component_type, page, component, name):
    """Add a component to an existing project."""
    try:
        p = Path(project_path).resolve()
        if not p.exists():
            click.secho(f"  Project not found: {project_path}", fg="red")
            sys.exit(1)

        comp_name = name or component_type
        if page:
            output_dir = p / "src" / "pages"
        elif component:
            output_dir = p / "src" / "components"
        else:
            output_dir = p / "src" / "components"

        output_dir.mkdir(parents=True, exist_ok=True)

        from streamlitforge.llm.providers.pattern_library import PatternLibraryProvider
        from streamlitforge.llm.base import Message, MessageRole

        plp = PatternLibraryProvider(
            library_path=str(Path(__file__).parent / "patterns")
        )
        resp = plp.generate([Message(MessageRole.USER, f"create {component_type} {comp_name}")])

        output_file = output_dir / f"{comp_name}.py"
        output_file.write_text(resp.content)

        click.secho(f"  Component added: {output_file}", fg="green")

    except Exception as e:
        click.secho(f"  Error: {e}", fg="red")
        sys.exit(1)


# ---------------------------------------------------------------------------
# update (knowledge base)
# ---------------------------------------------------------------------------

@cli.command()
@click.option("--force", is_flag=True, help="Update even if cache is fresh")
@click.option("--offline", is_flag=True, help="Only update from local patterns")
def update(force, offline):
    """Update the knowledge base."""
    try:
        from streamlitforge.knowledge.auto_update import AutoUpdatingKnowledgeBase

        kb = AutoUpdatingKnowledgeBase()
        if offline:
            click.echo("  Offline mode — using local patterns only.")
            return
        if force:
            results = kb.force_update()
        else:
            results = kb.update_if_stale()

        updated = sum(1 for v in results.values() if v)
        click.secho(f"  Knowledge base updated: {updated}/{len(results)} sources", fg="green")

    except Exception as e:
        click.secho(f"  Error: {e}", fg="red")
        sys.exit(1)


# ---------------------------------------------------------------------------
# config
# ---------------------------------------------------------------------------

@cli.command("config")
@click.option("--set", "set_kv", nargs=2, help="Set configuration value (key value)")
@click.option("--get", "get_key", help="Get configuration value")
@click.option("--init-config", is_flag=True, help="Initialize configuration file")
def config_cmd(set_kv, get_key, init_config):
    """Manage StreamlitForge configuration."""
    try:
        config_path = Path.home() / ".streamlitforge" / "config.yaml"

        if init_config:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            if config_path.exists():
                click.secho(f"  Config already exists: {config_path}", fg="yellow")
                return
            config = Config()
            config.load_from_dict({
                "llm": {"strategy": "cost_optimized"},
                "projects": {"default_template": "dashboard", "auto_git_init": True},
            })
            config.save_to_file(str(config_path), format="yaml")
            click.secho(f"  Config created: {config_path}", fg="green")

        elif set_kv:
            key, value = set_kv
            config = Config()
            if config_path.exists():
                config.load_from_file(str(config_path))
            config.set(key, value)
            config.save_to_file(str(config_path), format="yaml")
            click.secho(f"  Set {key} = {value}", fg="green")

        elif get_key:
            config = Config()
            if config_path.exists():
                config.load_from_file(str(config_path))
            value = config.get(get_key)
            if value is not None:
                click.echo(f"  {get_key} = {value}")
            else:
                click.echo(f"  {get_key} not set")

        else:
            if config_path.exists():
                click.echo(config_path.read_text())
            else:
                click.echo("  No configuration file found. Run: streamlitforge config --init-config")

    except Exception as e:
        click.secho(f"  Error: {e}", fg="red")
        sys.exit(1)


# ---------------------------------------------------------------------------
# keys
# ---------------------------------------------------------------------------

@cli.group()
def keys():
    """API key management."""
    pass


@keys.command("add")
@click.argument("provider")
@click.argument("key")
def keys_add(provider, key):
    """Add an API key for a provider."""
    try:
        from streamlitforge.core.api_keys import APIKeyManager
        mgr = APIKeyManager()
        mgr.set(provider, key)
        click.secho(f"  Key added for {provider}", fg="green")
    except Exception as e:
        click.secho(f"  Error: {e}", fg="red")
        sys.exit(1)


@keys.command("list")
def keys_list():
    """List configured API keys."""
    try:
        from streamlitforge.core.api_keys import APIKeyManager
        mgr = APIKeyManager()
        configured = mgr.list_configured()
        if not configured:
            click.echo("  No API keys configured.")
            click.echo("  Add keys with: streamlitforge keys add <provider> <key>")
            return
        click.secho("Configured providers:", fg="cyan")
        for p in configured:
            key = mgr.get(p) or ""
            masked = key[:4] + "..." + key[-4:] if len(key) > 8 else "****"
            click.echo(f"  {p}: {masked}")
    except Exception as e:
        click.secho(f"  Error: {e}", fg="red")
        sys.exit(1)


@keys.command("test")
@click.argument("provider", required=False)
def keys_test(provider):
    """Test API key(s)."""
    try:
        from streamlitforge.core.api_keys import APIKeyManager
        mgr = APIKeyManager()
        providers = [provider] if provider else mgr.list_configured()
        for p in providers:
            if mgr.has(p):
                click.secho(f"  {p}: configured ✓", fg="green")
            else:
                click.secho(f"  {p}: not configured ✗", fg="red")
    except Exception as e:
        click.secho(f"  Error: {e}", fg="red")
        sys.exit(1)


@keys.command("remove")
@click.argument("provider")
def keys_remove(provider):
    """Remove an API key."""
    try:
        from streamlitforge.core.api_keys import APIKeyManager
        mgr = APIKeyManager()
        mgr.remove(provider)
        click.secho(f"  Key removed for {provider}", fg="green")
    except Exception as e:
        click.secho(f"  Error: {e}", fg="red")
        sys.exit(1)


# ---------------------------------------------------------------------------
# knowledge (search)
# ---------------------------------------------------------------------------

@cli.group()
def knowledge():
    """Knowledge base commands."""
    pass


@knowledge.command()
@click.option("--query", "-q", help="Search query (interactive prompt if omitted)")
def search(query):
    """Search the knowledge base."""
    try:
        if not query:
            query = click.prompt("Enter search query")
        if not query:
            click.secho("  Query cannot be empty", fg="red")
            sys.exit(1)
        kb = BuiltInKnowledgeBase()
        results = kb.search_examples(query, limit=5)
        click.secho(f"\nSearch Results for: '{query}'", fg="cyan")
        click.echo()
        if not results:
            click.echo("  No results found.")
            return
        for i, result in enumerate(results, 1):
            click.secho(f"{i}. {result['title']}", fg="yellow")
            click.echo(f"   Category: {result['category']}")
            click.echo()
    except Exception as e:
        click.secho(f"  Error: {e}", fg="red")
        sys.exit(1)


# ---------------------------------------------------------------------------
# test
# ---------------------------------------------------------------------------

@cli.command()
def test():
    """Run the StreamlitForge test suite."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "streamlitforge/tests/", "-v"],
            capture_output=False,
        )
        sys.exit(result.returncode)
    except Exception as e:
        click.secho(f"  Error running tests: {e}", fg="red")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()

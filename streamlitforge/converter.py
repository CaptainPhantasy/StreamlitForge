"""CLI-to-Enterprise Converter — transforms CLI scripts to Streamlit apps."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ConversionOptions:
    add_sidebar: bool = True
    add_progress_bar: bool = True
    add_export: bool = True
    add_dark_mode: bool = True
    add_auth: bool = False
    auth_provider: str = "streamlit"
    add_logging: bool = True
    add_metrics: bool = False
    export_formats: List[str] = field(default_factory=lambda: ["csv", "json"])
    add_visualizations: bool = True
    add_error_handling: bool = True
    add_input_validation: bool = True
    add_tooltips: bool = True


@dataclass
class CLIArgument:
    name: str
    arg_type: str = "str"
    default: Any = None
    help_text: str = ""
    choices: Optional[List[str]] = None
    is_flag: bool = False
    is_file: bool = False


@dataclass
class ConversionResult:
    output_path: str
    files_created: List[str] = field(default_factory=list)
    cli_args_converted: int = 0
    warnings: List[str] = field(default_factory=list)


class CLIToEnterpriseConverter:
    """Converts CLI applications to Streamlit enterprise apps."""

    WIDGET_MAPPING = {
        "bool": "st.checkbox",
        "int": "st.number_input",
        "float": "st.number_input",
        "str": "st.text_input",
        "file": "st.file_uploader",
        "choice": "st.selectbox",
    }

    def __init__(self):
        pass

    def parse_cli_script(self, script_path: str) -> List[CLIArgument]:
        import ast
        try:
            with open(script_path) as f:
                code = f.read()
            tree = ast.parse(code)
        except (OSError, SyntaxError):
            return []

        args: List[CLIArgument] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == "add_argument":
                    arg = self._parse_add_argument(node)
                    if arg:
                        args.append(arg)
        return args

    def _parse_add_argument(self, node) -> Optional[CLIArgument]:
        import ast
        name = ""
        for a in node.args:
            if isinstance(a, ast.Constant) and isinstance(a.value, str):
                name = a.value.lstrip("-").replace("-", "_")
                break
        if not name:
            return None
        arg = CLIArgument(name=name)
        for kw in node.keywords:
            if kw.arg == "type" and isinstance(kw.value, ast.Name):
                arg.arg_type = kw.value.id
            elif kw.arg == "default" and isinstance(kw.value, ast.Constant):
                arg.default = kw.value.value
            elif kw.arg == "help" and isinstance(kw.value, ast.Constant):
                arg.help_text = kw.value.value
            elif kw.arg == "choices":
                if isinstance(kw.value, ast.List):
                    arg.choices = [
                        e.value for e in kw.value.elts if isinstance(e, ast.Constant)
                    ]
            elif kw.arg == "action" and isinstance(kw.value, ast.Constant):
                if kw.value.value in ("store_true", "store_false"):
                    arg.is_flag = True
                    arg.arg_type = "bool"
        return arg

    def map_to_widgets(self, args: List[CLIArgument]) -> Dict[str, Dict[str, Any]]:
        mapping: Dict[str, Dict[str, Any]] = {}
        for arg in args:
            if arg.is_flag:
                widget = "st.checkbox"
            elif arg.choices:
                widget = "st.selectbox"
            elif arg.is_file:
                widget = "st.file_uploader"
            else:
                widget = self.WIDGET_MAPPING.get(arg.arg_type, "st.text_input")

            params: Dict[str, Any] = {"label": arg.help_text or arg.name}
            if arg.default is not None:
                params["value"] = arg.default
            if arg.choices:
                params["options"] = arg.choices
            if arg.arg_type == "int":
                params["step"] = 1
            elif arg.arg_type == "float":
                params["step"] = 0.01

            mapping[arg.name] = {"widget": widget, "params": params}
        return mapping

    def generate_app(
        self,
        cli_script: str,
        output_path: str,
        options: Optional[ConversionOptions] = None,
    ) -> ConversionResult:
        options = options or ConversionOptions()
        args = self.parse_cli_script(cli_script)
        widgets = self.map_to_widgets(args)

        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)

        app_code = self._generate_app_code(widgets, options)
        app_file = output_dir / "app.py"
        app_file.write_text(app_code)

        files_created = [str(app_file)]

        req_file = output_dir / "requirements.txt"
        req_file.write_text("streamlit\npandas\n")
        files_created.append(str(req_file))

        return ConversionResult(
            output_path=str(output_dir),
            files_created=files_created,
            cli_args_converted=len(args),
        )

    def _generate_app_code(
        self, widgets: Dict[str, Dict[str, Any]], options: ConversionOptions
    ) -> str:
        lines = [
            "import streamlit as st",
            "",
            'st.set_page_config(page_title="Converted App", page_icon="🔄", layout="wide")',
            "",
            'st.title("Converted CLI Application")',
            "",
        ]

        if options.add_sidebar:
            lines.append("with st.sidebar:")
            lines.append('    st.header("Parameters")')
            for name, config in widgets.items():
                widget = config["widget"]
                params = config["params"]
                label = params.get("label", name)
                if widget == "st.checkbox":
                    lines.append(f'    {name} = st.checkbox("{label}")')
                elif widget == "st.selectbox":
                    opts = params.get("options", [])
                    lines.append(f'    {name} = st.selectbox("{label}", {opts})')
                elif widget == "st.number_input":
                    val = params.get("value", 0)
                    step = params.get("step", 1)
                    lines.append(f'    {name} = st.number_input("{label}", value={val}, step={step})')
                elif widget == "st.file_uploader":
                    lines.append(f'    {name} = st.file_uploader("{label}")')
                else:
                    val = params.get("value", "")
                    lines.append(f'    {name} = st.text_input("{label}", value="{val}")')
            lines.append("")

        lines.append('if st.button("Run"):')
        if options.add_progress_bar:
            lines.append("    progress = st.progress(0)")
            lines.append("    progress.progress(50)")
        lines.append('    st.success("Processing complete!")')
        if options.add_progress_bar:
            lines.append("    progress.progress(100)")

        if options.add_export:
            lines.append("")
            lines.append('    st.download_button("Download Results", "results", "results.txt")')

        return "\n".join(lines) + "\n"

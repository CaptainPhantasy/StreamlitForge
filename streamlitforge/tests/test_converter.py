"""Tests for CLIToEnterpriseConverter — no mocks, real functional calls."""

import os
import tempfile
import unittest
from pathlib import Path

from streamlitforge.converter import (
    CLIToEnterpriseConverter,
    ConversionOptions,
    CLIArgument,
    ConversionResult,
)


class TestConversionOptions(unittest.TestCase):
    def test_default_options(self):
        opts = ConversionOptions()
        self.assertTrue(opts.add_sidebar)
        self.assertTrue(opts.add_progress_bar)
        self.assertTrue(opts.add_export)
        self.assertTrue(opts.add_dark_mode)
        self.assertFalse(opts.add_auth)
        self.assertEqual(opts.auth_provider, "streamlit")
        self.assertTrue(opts.add_logging)
        self.assertFalse(opts.add_metrics)
        self.assertEqual(opts.export_formats, ["csv", "json"])

    def test_custom_options(self):
        opts = ConversionOptions(add_sidebar=False, add_auth=True, export_formats=["xlsx"])
        self.assertFalse(opts.add_sidebar)
        self.assertTrue(opts.add_auth)
        self.assertEqual(opts.export_formats, ["xlsx"])


class TestCLIArgument(unittest.TestCase):
    def test_default_values(self):
        arg = CLIArgument(name="test")
        self.assertEqual(arg.name, "test")
        self.assertEqual(arg.arg_type, "str")
        self.assertIsNone(arg.default)
        self.assertEqual(arg.help_text, "")
        self.assertIsNone(arg.choices)
        self.assertFalse(arg.is_flag)
        self.assertFalse(arg.is_file)

    def test_custom_values(self):
        arg = CLIArgument(name="count", arg_type="int", default=10, help_text="Number of items")
        self.assertEqual(arg.arg_type, "int")
        self.assertEqual(arg.default, 10)
        self.assertEqual(arg.help_text, "Number of items")


class TestConversionResult(unittest.TestCase):
    def test_default_values(self):
        result = ConversionResult(output_path="/tmp/test")
        self.assertEqual(result.output_path, "/tmp/test")
        self.assertEqual(result.files_created, [])
        self.assertEqual(result.cli_args_converted, 0)
        self.assertEqual(result.warnings, [])


class TestWidgetMapping(unittest.TestCase):
    def setUp(self):
        self.converter = CLIToEnterpriseConverter()

    def test_bool_maps_to_checkbox(self):
        self.assertEqual(self.converter.WIDGET_MAPPING["bool"], "st.checkbox")

    def test_int_maps_to_number_input(self):
        self.assertEqual(self.converter.WIDGET_MAPPING["int"], "st.number_input")

    def test_float_maps_to_number_input(self):
        self.assertEqual(self.converter.WIDGET_MAPPING["float"], "st.number_input")

    def test_str_maps_to_text_input(self):
        self.assertEqual(self.converter.WIDGET_MAPPING["str"], "st.text_input")

    def test_file_maps_to_file_uploader(self):
        self.assertEqual(self.converter.WIDGET_MAPPING["file"], "st.file_uploader")

    def test_choice_maps_to_selectbox(self):
        self.assertEqual(self.converter.WIDGET_MAPPING["choice"], "st.selectbox")


class TestMapToWidgets(unittest.TestCase):
    def setUp(self):
        self.converter = CLIToEnterpriseConverter()

    def test_str_argument(self):
        args = [CLIArgument(name="name", arg_type="str", help_text="Your name")]
        mapping = self.converter.map_to_widgets(args)
        self.assertIn("name", mapping)
        self.assertEqual(mapping["name"]["widget"], "st.text_input")
        self.assertEqual(mapping["name"]["params"]["label"], "Your name")

    def test_int_argument_has_step(self):
        args = [CLIArgument(name="count", arg_type="int", default=5)]
        mapping = self.converter.map_to_widgets(args)
        self.assertEqual(mapping["count"]["params"]["step"], 1)
        self.assertEqual(mapping["count"]["params"]["value"], 5)

    def test_float_argument_has_step(self):
        args = [CLIArgument(name="rate", arg_type="float")]
        mapping = self.converter.map_to_widgets(args)
        self.assertEqual(mapping["rate"]["params"]["step"], 0.01)

    def test_flag_argument_maps_to_checkbox(self):
        args = [CLIArgument(name="verbose", is_flag=True)]
        mapping = self.converter.map_to_widgets(args)
        self.assertEqual(mapping["verbose"]["widget"], "st.checkbox")

    def test_choice_argument_maps_to_selectbox(self):
        args = [CLIArgument(name="color", choices=["red", "blue", "green"])]
        mapping = self.converter.map_to_widgets(args)
        self.assertEqual(mapping["color"]["widget"], "st.selectbox")
        self.assertEqual(mapping["color"]["params"]["options"], ["red", "blue", "green"])

    def test_file_argument(self):
        args = [CLIArgument(name="input_file", is_file=True)]
        mapping = self.converter.map_to_widgets(args)
        self.assertEqual(mapping["input_file"]["widget"], "st.file_uploader")

    def test_empty_args(self):
        mapping = self.converter.map_to_widgets([])
        self.assertEqual(mapping, {})

    def test_label_falls_back_to_name(self):
        args = [CLIArgument(name="output")]
        mapping = self.converter.map_to_widgets(args)
        self.assertEqual(mapping["output"]["params"]["label"], "output")


class TestParseCLIScript(unittest.TestCase):
    def setUp(self):
        self.converter = CLIToEnterpriseConverter()
        self.tmp = tempfile.mkdtemp()

    def test_parse_argparse_script(self):
        script = Path(self.tmp) / "cli_script.py"
        script.write_text('''
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--name", type=str, default="World", help="Your name")
parser.add_argument("--count", type=int, default=1, help="Repeat count")
parser.add_argument("--verbose", action="store_true", help="Verbose output")
args = parser.parse_args()
''')
        args = self.converter.parse_cli_script(str(script))
        names = [a.name for a in args]
        self.assertIn("name", names)
        self.assertIn("count", names)
        self.assertIn("verbose", names)

    def test_parse_detects_types(self):
        script = Path(self.tmp) / "typed.py"
        script.write_text('''
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--rate", type=float, default=0.5, help="Rate")
args = parser.parse_args()
''')
        args = self.converter.parse_cli_script(str(script))
        self.assertEqual(len(args), 1)
        self.assertEqual(args[0].arg_type, "float")
        self.assertEqual(args[0].default, 0.5)

    def test_parse_detects_choices(self):
        script = Path(self.tmp) / "choices.py"
        script.write_text('''
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--color", choices=["red", "blue"])
args = parser.parse_args()
''')
        args = self.converter.parse_cli_script(str(script))
        self.assertEqual(len(args), 1)
        self.assertEqual(args[0].choices, ["red", "blue"])

    def test_parse_detects_store_true(self):
        script = Path(self.tmp) / "flags.py"
        script.write_text('''
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--debug", action="store_true")
args = parser.parse_args()
''')
        args = self.converter.parse_cli_script(str(script))
        self.assertEqual(len(args), 1)
        self.assertTrue(args[0].is_flag)
        self.assertEqual(args[0].arg_type, "bool")

    def test_parse_nonexistent_returns_empty(self):
        args = self.converter.parse_cli_script("/nonexistent/path.py")
        self.assertEqual(args, [])

    def test_parse_syntax_error_returns_empty(self):
        script = Path(self.tmp) / "bad.py"
        script.write_text("def foo(:\n  pass\n")
        args = self.converter.parse_cli_script(str(script))
        self.assertEqual(args, [])

    def test_parse_empty_script_returns_empty(self):
        script = Path(self.tmp) / "empty.py"
        script.write_text("# no argparse here\nprint('hello')\n")
        args = self.converter.parse_cli_script(str(script))
        self.assertEqual(args, [])


class TestGenerateApp(unittest.TestCase):
    def setUp(self):
        self.converter = CLIToEnterpriseConverter()
        self.tmp = tempfile.mkdtemp()
        self.script_path = os.path.join(self.tmp, "cli.py")
        Path(self.script_path).write_text('''
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--name", type=str, default="World", help="Your name")
parser.add_argument("--count", type=int, default=3, help="Repeat count")
args = parser.parse_args()
''')

    def test_returns_conversion_result(self):
        output = os.path.join(self.tmp, "output")
        result = self.converter.generate_app(self.script_path, output)
        self.assertIsInstance(result, ConversionResult)

    def test_creates_output_dir(self):
        output = os.path.join(self.tmp, "output")
        self.converter.generate_app(self.script_path, output)
        self.assertTrue(Path(output).is_dir())

    def test_creates_app_py(self):
        output = os.path.join(self.tmp, "output")
        result = self.converter.generate_app(self.script_path, output)
        app_file = Path(output) / "app.py"
        self.assertTrue(app_file.exists())
        self.assertTrue(any("app.py" in f for f in result.files_created))

    def test_creates_requirements_txt(self):
        output = os.path.join(self.tmp, "output")
        result = self.converter.generate_app(self.script_path, output)
        req_file = Path(output) / "requirements.txt"
        self.assertTrue(req_file.exists())
        content = req_file.read_text()
        self.assertIn("streamlit", content)

    def test_app_has_streamlit_import(self):
        output = os.path.join(self.tmp, "output")
        self.converter.generate_app(self.script_path, output)
        content = (Path(output) / "app.py").read_text()
        self.assertIn("import streamlit as st", content)

    def test_app_has_set_page_config(self):
        output = os.path.join(self.tmp, "output")
        self.converter.generate_app(self.script_path, output)
        content = (Path(output) / "app.py").read_text()
        self.assertIn("st.set_page_config", content)

    def test_app_has_sidebar_with_widgets(self):
        output = os.path.join(self.tmp, "output")
        self.converter.generate_app(self.script_path, output)
        content = (Path(output) / "app.py").read_text()
        self.assertIn("st.sidebar", content)

    def test_app_has_run_button(self):
        output = os.path.join(self.tmp, "output")
        self.converter.generate_app(self.script_path, output)
        content = (Path(output) / "app.py").read_text()
        self.assertIn('st.button("Run")', content)

    def test_app_has_progress_bar(self):
        output = os.path.join(self.tmp, "output")
        self.converter.generate_app(self.script_path, output)
        content = (Path(output) / "app.py").read_text()
        self.assertIn("st.progress", content)

    def test_app_has_download_button(self):
        output = os.path.join(self.tmp, "output")
        self.converter.generate_app(self.script_path, output)
        content = (Path(output) / "app.py").read_text()
        self.assertIn("st.download_button", content)

    def test_cli_args_converted_count(self):
        output = os.path.join(self.tmp, "output")
        result = self.converter.generate_app(self.script_path, output)
        self.assertEqual(result.cli_args_converted, 2)

    def test_no_sidebar_option(self):
        output = os.path.join(self.tmp, "output")
        opts = ConversionOptions(add_sidebar=False)
        self.converter.generate_app(self.script_path, output, options=opts)
        content = (Path(output) / "app.py").read_text()
        self.assertNotIn("st.sidebar", content)

    def test_no_progress_option(self):
        output = os.path.join(self.tmp, "output2")
        opts = ConversionOptions(add_progress_bar=False)
        self.converter.generate_app(self.script_path, output, options=opts)
        content = (Path(output) / "app.py").read_text()
        self.assertNotIn("st.progress", content)

    def test_no_export_option(self):
        output = os.path.join(self.tmp, "output3")
        opts = ConversionOptions(add_export=False)
        self.converter.generate_app(self.script_path, output, options=opts)
        content = (Path(output) / "app.py").read_text()
        self.assertNotIn("st.download_button", content)


if __name__ == "__main__":
    unittest.main()

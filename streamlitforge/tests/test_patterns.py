"""Tests for PatternLearner — no mocks, real functional calls."""

import json
import os
import tempfile
import unittest
from pathlib import Path

from streamlitforge.patterns.learner import PatternLearner
from streamlitforge.patterns.examples import CHAT_PATTERN, DASHBOARD_PATTERN


class TestPatternLearnerInit(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.lib_path = os.path.join(self.tmp, "patterns")

    def test_creates_library_dir(self):
        pl = PatternLearner(library_path=self.lib_path)
        self.assertTrue(Path(self.lib_path).is_dir())

    def test_default_min_examples(self):
        pl = PatternLearner(library_path=self.lib_path)
        self.assertEqual(pl.min_examples, 3)

    def test_custom_min_examples(self):
        pl = PatternLearner(library_path=self.lib_path, min_examples=5)
        self.assertEqual(pl.min_examples, 5)

    def test_initial_pattern_count_zero(self):
        pl = PatternLearner(library_path=self.lib_path)
        self.assertEqual(pl.get_pattern_count(), 0)


class TestExtractTriggers(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.pl = PatternLearner(library_path=os.path.join(self.tmp, "patterns"))

    def test_extracts_st_calls(self):
        code = "import streamlit as st\nst.title('Hello')\nst.write('World')"
        triggers = self.pl._extract_triggers(code)
        self.assertIn("title", triggers)
        self.assertIn("write", triggers)

    def test_extracts_from_chat_pattern(self):
        triggers = self.pl._extract_triggers(CHAT_PATTERN["template"])
        self.assertIn("title", triggers)
        self.assertIn("chat_message", triggers)
        self.assertIn("chat_input", triggers)

    def test_syntax_error_returns_partial(self):
        code = "st.title('hi')\ndef bad(:\n  pass"
        triggers = self.pl._extract_triggers(code)
        self.assertIn("title", triggers)

    def test_empty_code_returns_empty(self):
        triggers = self.pl._extract_triggers("")
        self.assertEqual(triggers, [])

    def test_no_st_calls_returns_empty(self):
        triggers = self.pl._extract_triggers("x = 1\ny = x + 2\n")
        self.assertEqual(triggers, [])

    def test_triggers_sorted(self):
        code = "import streamlit as st\nst.write('a')\nst.title('b')\nst.button('c')"
        triggers = self.pl._extract_triggers(code)
        self.assertEqual(triggers, sorted(triggers))


class TestExtractVariables(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.pl = PatternLearner(library_path=os.path.join(self.tmp, "patterns"))

    def test_extracts_string_literals(self):
        code = 'st.title("My Dashboard")\nst.write("Hello World")'
        variables = self.pl._extract_variables(code)
        self.assertGreater(len(variables), 0)

    def test_limits_to_five(self):
        code = "\n".join(f'st.write("line number {i} content")' for i in range(10))
        variables = self.pl._extract_variables(code)
        self.assertLessEqual(len(variables), 5)

    def test_skips_short_strings(self):
        code = 'x = "ab"'
        variables = self.pl._extract_variables(code)
        self.assertEqual(len(variables), 0)


class TestRecordSuccess(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.lib_path = os.path.join(self.tmp, "patterns")
        self.pl = PatternLearner(library_path=self.lib_path)

    def test_creates_pattern_file(self):
        self.pl.record_success(
            prompt="create a dashboard",
            generated_code="import streamlit as st\nst.title('Dashboard')\n",
        )
        self.assertEqual(self.pl.get_pattern_count(), 1)

    def test_pattern_file_has_json(self):
        self.pl.record_success(
            prompt="create a dashboard",
            generated_code="import streamlit as st\nst.title('Dashboard')\n",
        )
        files = list(Path(self.lib_path).glob("pattern_*.json"))
        self.assertEqual(len(files), 1)
        data = json.loads(files[0].read_text())
        self.assertIn("pattern_id", data)
        self.assertIn("triggers", data)
        self.assertIn("template", data)
        self.assertIn("examples", data)

    def test_records_usage_count(self):
        self.pl.record_success(
            prompt="create a dashboard",
            generated_code="import streamlit as st\nst.title('Dashboard')\n",
        )
        files = list(Path(self.lib_path).glob("pattern_*.json"))
        data = json.loads(files[0].read_text())
        self.assertEqual(data["usage_count"], 1)

    def test_records_last_used(self):
        self.pl.record_success(
            prompt="create a dashboard",
            generated_code="import streamlit as st\nst.title('Dashboard')\n",
        )
        files = list(Path(self.lib_path).glob("pattern_*.json"))
        data = json.loads(files[0].read_text())
        self.assertIn("last_used", data)

    def test_user_modifications_stored(self):
        self.pl.record_success(
            prompt="create a chart",
            generated_code="import streamlit as st\nst.line_chart([1,2,3])\n",
            user_modifications="import streamlit as st\nst.bar_chart([1,2,3])\n",
        )
        files = list(Path(self.lib_path).glob("pattern_*.json"))
        data = json.loads(files[0].read_text())
        self.assertIn("bar_chart", data["template"])

    def test_multiple_patterns_stored(self):
        self.pl.record_success(
            prompt="create a dashboard",
            generated_code="import streamlit as st\nst.title('Dashboard')\n",
        )
        self.pl.record_success(
            prompt="create a form xyz",
            generated_code="import streamlit as st\nst.form('form1')\n",
        )
        self.assertEqual(self.pl.get_pattern_count(), 2)


class TestFindPattern(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.lib_path = os.path.join(self.tmp, "patterns")
        self.pl = PatternLearner(library_path=self.lib_path)

    def test_returns_none_no_patterns(self):
        result = self.pl.find_pattern("anything")
        self.assertIsNone(result)

    def test_finds_matching_pattern(self):
        self.pl.record_success(
            prompt="create title write",
            generated_code="import streamlit as st\nst.title('Hi')\nst.write('Hello')\n",
        )
        result = self.pl.find_pattern("title write")
        self.assertIsNotNone(result)
        self.assertIn("st.title", result)

    def test_no_match_returns_none(self):
        self.pl.record_success(
            prompt="create title write",
            generated_code="import streamlit as st\nst.title('Hi')\n",
        )
        result = self.pl.find_pattern("xyzzy_totally_unrelated_query")
        self.assertIsNone(result)


class TestListPatterns(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.lib_path = os.path.join(self.tmp, "patterns")
        self.pl = PatternLearner(library_path=self.lib_path)

    def test_empty_list_initially(self):
        patterns = self.pl.list_patterns()
        self.assertEqual(patterns, [])

    def test_lists_created_patterns(self):
        self.pl.record_success(
            prompt="make a table",
            generated_code="import streamlit as st\nst.table([1,2,3])\n",
        )
        patterns = self.pl.list_patterns()
        self.assertEqual(len(patterns), 1)
        self.assertIn("pattern_id", patterns[0])
        self.assertIn("name", patterns[0])
        self.assertIn("triggers", patterns[0])
        self.assertIn("usage_count", patterns[0])

    def test_pattern_count_matches_list(self):
        self.pl.record_success(prompt="a", generated_code="import streamlit as st\nst.title('A')\n")
        self.pl.record_success(prompt="b xyz", generated_code="import streamlit as st\nst.write('B')\n")
        self.assertEqual(self.pl.get_pattern_count(), len(self.pl.list_patterns()))


class TestExamplePatterns(unittest.TestCase):
    def test_chat_pattern_has_required_fields(self):
        self.assertIn("name", CHAT_PATTERN)
        self.assertIn("template", CHAT_PATTERN)
        self.assertIn("category", CHAT_PATTERN)
        self.assertIn("description", CHAT_PATTERN)

    def test_dashboard_pattern_has_required_fields(self):
        self.assertIn("name", DASHBOARD_PATTERN)
        self.assertIn("template", DASHBOARD_PATTERN)
        self.assertIn("category", DASHBOARD_PATTERN)

    def test_chat_pattern_template_has_streamlit(self):
        self.assertIn("import streamlit as st", CHAT_PATTERN["template"])

    def test_dashboard_pattern_template_has_streamlit(self):
        self.assertIn("import streamlit as st", DASHBOARD_PATTERN["template"])


if __name__ == "__main__":
    unittest.main()

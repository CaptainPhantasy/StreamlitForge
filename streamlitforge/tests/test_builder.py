"""Tests for InteractiveBuilder — no mocks, real functional calls."""

import unittest

from streamlitforge.builder import (
    ConversationManager,
    CodePreviewManager,
    InteractiveBuilder,
)


class TestConversationManager(unittest.TestCase):
    def setUp(self):
        self.cm = ConversationManager(max_context_messages=5)

    def test_initial_messages_empty(self):
        self.assertEqual(self.cm.messages, [])

    def test_initial_mode_is_chat(self):
        self.assertEqual(self.cm.mode, "chat")

    def test_add_message(self):
        self.cm.add_message("user", "Hello")
        self.assertEqual(len(self.cm.messages), 1)
        self.assertEqual(self.cm.messages[0]["role"], "user")
        self.assertEqual(self.cm.messages[0]["content"], "Hello")

    def test_add_multiple_messages(self):
        self.cm.add_message("user", "Q1")
        self.cm.add_message("assistant", "A1")
        self.cm.add_message("user", "Q2")
        self.assertEqual(len(self.cm.messages), 3)

    def test_context_truncation(self):
        cm = ConversationManager(max_context_messages=3)
        for i in range(20):
            cm.add_message("user", f"msg {i}")
        context = cm.get_context()
        self.assertLessEqual(len(context), 3)

    def test_get_context_returns_recent(self):
        for i in range(10):
            self.cm.add_message("user", f"msg {i}")
        context = self.cm.get_context()
        last_content = context[-1]["content"]
        self.assertEqual(last_content, "msg 9")

    def test_set_mode_valid(self):
        self.cm.set_mode("build")
        self.assertEqual(self.cm.mode, "build")

    def test_set_mode_expert(self):
        self.cm.set_mode("expert")
        self.assertEqual(self.cm.mode, "expert")

    def test_set_mode_invalid_ignored(self):
        self.cm.set_mode("invalid_mode")
        self.assertEqual(self.cm.mode, "chat")

    def test_clear(self):
        self.cm.add_message("user", "Hello")
        self.cm.clear()
        self.assertEqual(self.cm.messages, [])

    def test_message_trimming_at_double_max(self):
        cm = ConversationManager(max_context_messages=3)
        for i in range(7):
            cm.add_message("user", f"msg {i}")
        self.assertLessEqual(len(cm.messages), 3)


class TestCodePreviewManager(unittest.TestCase):
    def setUp(self):
        self.cpm = CodePreviewManager()

    def test_initial_empty(self):
        self.assertEqual(self.cpm.code_blocks, [])

    def test_extract_single_block(self):
        content = "Here is code:\n```python\nimport streamlit as st\nst.title('Hi')\n```\nDone."
        blocks = self.cpm.extract_code(content)
        self.assertEqual(len(blocks), 1)
        self.assertIn("import streamlit", blocks[0])

    def test_extract_multiple_blocks(self):
        content = (
            "First:\n```python\ncode1()\n```\n"
            "Second:\n```python\ncode2()\n```\n"
        )
        blocks = self.cpm.extract_code(content)
        self.assertEqual(len(blocks), 2)

    def test_extract_no_blocks(self):
        blocks = self.cpm.extract_code("No code here.")
        self.assertEqual(blocks, [])

    def test_get_latest_code(self):
        self.cpm.extract_code("```python\nfirst()\n```")
        self.cpm.extract_code("```python\nsecond()\n```")
        latest = self.cpm.get_latest_code()
        self.assertIn("second()", latest)

    def test_get_latest_code_none_when_empty(self):
        self.assertIsNone(self.cpm.get_latest_code())

    def test_clear(self):
        self.cpm.extract_code("```python\ncode()\n```")
        self.cpm.clear()
        self.assertEqual(self.cpm.code_blocks, [])

    def test_extract_code_without_language_marker(self):
        content = "```\nbare_code()\n```"
        blocks = self.cpm.extract_code(content)
        self.assertEqual(len(blocks), 1)
        self.assertIn("bare_code()", blocks[0])

    def test_accumulated_blocks(self):
        self.cpm.extract_code("```python\na()\n```")
        self.cpm.extract_code("```python\nb()\n```")
        self.assertEqual(len(self.cpm.code_blocks), 2)


class TestInteractiveBuilder(unittest.TestCase):
    def setUp(self):
        self.builder = InteractiveBuilder()

    def test_has_conversation_manager(self):
        self.assertIsInstance(self.builder.conversation, ConversationManager)

    def test_has_code_preview(self):
        self.assertIsInstance(self.builder.code_preview, CodePreviewManager)

    def test_modes_defined(self):
        self.assertIn("chat", self.builder.MODES)
        self.assertIn("build", self.builder.MODES)
        self.assertIn("expert", self.builder.MODES)

    def test_get_system_prompt_chat(self):
        prompt = self.builder.get_system_prompt("chat")
        self.assertIn("StreamlitForge Assistant", prompt)

    def test_get_system_prompt_build(self):
        prompt = self.builder.get_system_prompt("build")
        self.assertIn("StreamlitForge Builder", prompt)

    def test_get_system_prompt_expert(self):
        prompt = self.builder.get_system_prompt("expert")
        self.assertIn("Senior Streamlit Developer", prompt)

    def test_get_system_prompt_default_is_chat(self):
        prompt = self.builder.get_system_prompt()
        self.assertIn("StreamlitForge Assistant", prompt)

    def test_process_input_returns_dict(self):
        result = self.builder.process_input("Hello")
        self.assertIsInstance(result, dict)
        self.assertIn("mode", result)
        self.assertIn("system_prompt", result)
        self.assertIn("messages", result)
        self.assertIn("temperature", result)

    def test_process_input_adds_message(self):
        self.builder.process_input("Hello")
        self.assertEqual(len(self.builder.conversation.messages), 1)

    def test_process_input_chat_temperature(self):
        result = self.builder.process_input("Hello", mode="chat")
        self.assertEqual(result["temperature"], 0.7)

    def test_process_input_build_temperature(self):
        result = self.builder.process_input("Generate code", mode="build")
        self.assertEqual(result["temperature"], 0.3)

    def test_process_input_expert_temperature(self):
        result = self.builder.process_input("Review my code", mode="expert")
        self.assertEqual(result["temperature"], 0.5)

    def test_process_input_messages_included(self):
        result = self.builder.process_input("Hello")
        self.assertTrue(any(m["content"] == "Hello" for m in result["messages"]))

    def test_render_streamlit_ui_returns_code(self):
        code = self.builder.render_streamlit_ui()
        self.assertIn("import streamlit as st", code)
        self.assertIn("st.set_page_config", code)
        self.assertIn("st.chat_input", code)


if __name__ == "__main__":
    unittest.main()

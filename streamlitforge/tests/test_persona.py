"""Tests for SeniorDeveloperPersona — no mocks, real functional calls."""

import unittest

from streamlitforge.persona import SeniorDeveloperPersona, SENIOR_DEVELOPER_PROMPT


class TestSeniorDeveloperPrompt(unittest.TestCase):
    def test_prompt_is_string(self):
        self.assertIsInstance(SENIOR_DEVELOPER_PROMPT, str)

    def test_prompt_not_empty(self):
        self.assertGreater(len(SENIOR_DEVELOPER_PROMPT), 100)

    def test_prompt_mentions_streamlit(self):
        self.assertIn("Streamlit", SENIOR_DEVELOPER_PROMPT)

    def test_prompt_mentions_mentor(self):
        self.assertIn("mentor", SENIOR_DEVELOPER_PROMPT)


class TestDomains(unittest.TestCase):
    def setUp(self):
        self.persona = SeniorDeveloperPersona()

    def test_has_five_domains(self):
        self.assertEqual(len(self.persona.DOMAINS), 5)

    def test_each_domain_has_items(self):
        for domain, items in self.persona.DOMAINS.items():
            self.assertIsInstance(items, list)
            self.assertGreater(len(items), 0, f"Domain {domain} has no items")

    def test_architecture_domain_exists(self):
        self.assertIn("architecture", self.persona.DOMAINS)

    def test_performance_domain_exists(self):
        self.assertIn("performance", self.persona.DOMAINS)

    def test_security_domain_exists(self):
        self.assertIn("security", self.persona.DOMAINS)

    def test_deployment_domain_exists(self):
        self.assertIn("deployment", self.persona.DOMAINS)

    def test_patterns_domain_exists(self):
        self.assertIn("patterns", self.persona.DOMAINS)


class TestDomainKeywords(unittest.TestCase):
    def setUp(self):
        self.persona = SeniorDeveloperPersona()

    def test_keywords_match_domains(self):
        for domain in self.persona.DOMAINS:
            self.assertIn(domain, self.persona.DOMAIN_KEYWORDS,
                          f"No keywords for domain {domain}")

    def test_each_keyword_list_nonempty(self):
        for domain, keywords in self.persona.DOMAIN_KEYWORDS.items():
            self.assertGreater(len(keywords), 0, f"Domain {domain} has no keywords")


class TestDetectDomain(unittest.TestCase):
    def setUp(self):
        self.persona = SeniorDeveloperPersona()

    def test_detects_architecture(self):
        result = self.persona.detect_domain("How do I structure a multi-page app?")
        self.assertEqual(result, "architecture")

    def test_detects_performance(self):
        result = self.persona.detect_domain("My app is slow, how do I optimize and cache?")
        self.assertEqual(result, "performance")

    def test_detects_security(self):
        result = self.persona.detect_domain("How do I handle auth and passwords securely?")
        self.assertEqual(result, "security")

    def test_detects_deployment(self):
        result = self.persona.detect_domain("How do I deploy with docker to the cloud?")
        self.assertEqual(result, "deployment")

    def test_detects_patterns(self):
        result = self.persona.detect_domain("What pattern should I use, like a factory pattern?")
        self.assertEqual(result, "patterns")

    def test_default_fallback_is_architecture(self):
        result = self.persona.detect_domain("random nonsense with no keywords at all xyzzy")
        self.assertEqual(result, "architecture")

    def test_case_insensitive(self):
        result = self.persona.detect_domain("DEPLOY to DOCKER on KUBERNETES")
        self.assertEqual(result, "deployment")


class TestGetSystemPrompt(unittest.TestCase):
    def setUp(self):
        self.persona = SeniorDeveloperPersona()

    def test_base_prompt_included(self):
        prompt = self.persona.get_system_prompt()
        self.assertIn("Senior Streamlit Developer", prompt)

    def test_domain_focus_included(self):
        prompt = self.persona.get_system_prompt(domain="security")
        self.assertIn("security", prompt)
        self.assertIn("Relevant patterns", prompt)

    def test_unknown_domain_returns_base_only(self):
        prompt = self.persona.get_system_prompt(domain="nonexistent")
        self.assertNotIn("Focus on:", prompt)

    def test_no_domain_returns_base(self):
        prompt = self.persona.get_system_prompt()
        self.assertNotIn("Focus on:", prompt)

    def test_each_valid_domain_adds_focus(self):
        for domain in self.persona.DOMAINS:
            prompt = self.persona.get_system_prompt(domain=domain)
            self.assertIn(f"Focus on: {domain}", prompt)


class TestGetReviewPrompt(unittest.TestCase):
    def setUp(self):
        self.persona = SeniorDeveloperPersona()

    def test_review_contains_code(self):
        code = "import streamlit as st\nst.title('Hello')"
        prompt = self.persona.get_review_prompt(code)
        self.assertIn(code, prompt)

    def test_review_asks_for_assessment(self):
        prompt = self.persona.get_review_prompt("print('hi')")
        self.assertIn("Overall assessment", prompt)

    def test_review_asks_for_security(self):
        prompt = self.persona.get_review_prompt("print('hi')")
        self.assertIn("Security concerns", prompt)

    def test_review_asks_for_performance(self):
        prompt = self.persona.get_review_prompt("print('hi')")
        self.assertIn("Performance suggestions", prompt)

    def test_review_asks_for_best_practices(self):
        prompt = self.persona.get_review_prompt("print('hi')")
        self.assertIn("Best practice violations", prompt)

    def test_review_wraps_code_in_python_block(self):
        prompt = self.persona.get_review_prompt("x = 1")
        self.assertIn("```python", prompt)
        self.assertIn("```", prompt)


if __name__ == "__main__":
    unittest.main()

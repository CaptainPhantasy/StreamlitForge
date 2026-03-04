"""Test Configuration System — real functional tests (no mocks)."""

import json
import os
import tempfile
import unittest
from pathlib import Path

from streamlitforge.core.config import Config, ConfigError


class TestConfigDefaults(unittest.TestCase):
    """Test Config with default values."""

    def test_empty_config_has_empty_dict(self):
        config = Config()
        self.assertIsInstance(config.config, dict)

    def test_get_with_default_on_empty(self):
        config = Config()
        self.assertEqual(config.get('nonexistent', 42), 42)

    def test_set_and_get(self):
        config = Config()
        config.set('project_name', 'MyApp')
        self.assertEqual(config.get('project_name'), 'MyApp')


class TestConfigLoadFromDict(unittest.TestCase):
    """Test loading config from a dictionary."""

    def test_load_basic_dict(self):
        config = Config()
        config.load_from_dict({
            'project_name': 'TestProject',
            'port': 8502,
            'dependencies': ['pandas'],
        })
        self.assertEqual(config.get('project_name'), 'TestProject')
        self.assertEqual(config.get('port'), 8502)
        self.assertEqual(config.get('dependencies'), ['pandas'])

    def test_defaults_filled_in(self):
        config = Config()
        config.load_from_dict({'project_name': 'TestProject'})
        self.assertEqual(config.get('port'), 8501)

    def test_unknown_key_raises(self):
        config = Config()
        with self.assertRaises(ConfigError):
            config.load_from_dict({'bogus_key': 'value'})

    def test_embedding_dim_384_accepted(self):
        config = Config()
        config.load_from_dict({
            'knowledge': {
                'embedding_dim': 384,
                'max_examples': 10,
            }
        })
        self.assertEqual(config.get('knowledge.embedding_dim'), 384)

    def test_embedding_dim_zero_rejected(self):
        config = Config()
        with self.assertRaises(ConfigError):
            config.load_from_dict({
                'knowledge': {'embedding_dim': 0}
            })


class TestConfigDotNotation(unittest.TestCase):
    """Test dot-notation get/set on nested config."""

    def test_nested_get(self):
        config = Config()
        config.load_from_dict({'llm': {'provider': 'ollama', 'model': 'llama3'}})
        self.assertEqual(config.get('llm.provider'), 'ollama')
        self.assertEqual(config.get('llm.model'), 'llama3')

    def test_nested_set(self):
        config = Config()
        config.set('llm', {'provider': 'openrouter', 'model': 'test'})
        config.set('llm.model', 'gpt-4')
        self.assertEqual(config.get('llm.model'), 'gpt-4')


class TestConfigValidation(unittest.TestCase):
    """Test validation rules."""

    def test_invalid_port_zero(self):
        config = Config()
        config.set('port', 0)
        with self.assertRaises(ConfigError):
            config._validate()

    def test_invalid_project_name_starts_with_digit(self):
        config = Config()
        config.set('project_name', '12invalid')
        with self.assertRaises(ConfigError):
            config._validate()

    def test_invalid_llm_provider(self):
        config = Config()
        with self.assertRaises(ConfigError):
            config.load_from_dict({'llm': {'provider': 'fake_provider'}})

    def test_temperature_out_of_range(self):
        config = Config()
        with self.assertRaises(ConfigError):
            config.load_from_dict({'llm': {'temperature': 3.0}})

    def test_max_tokens_out_of_range(self):
        config = Config()
        with self.assertRaises(ConfigError):
            config.load_from_dict({'llm': {'max_tokens': 99999}})


class TestConfigFileIO(unittest.TestCase):
    """Test save/load round-trip with real files."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_yaml_round_trip(self):
        path = os.path.join(self.tmp_dir, 'config.yaml')
        c1 = Config()
        c1.load_from_dict({'project_name': 'YamlTest', 'port': 8510})
        c1.save_to_file(path, format='yaml')

        c2 = Config(config_path=path)
        self.assertEqual(c2.get('project_name'), 'YamlTest')
        self.assertEqual(c2.get('port'), 8510)

    def test_json_round_trip(self):
        path = os.path.join(self.tmp_dir, 'config.json')
        c1 = Config()
        c1.load_from_dict({'project_name': 'JsonTest', 'port': 8520})
        c1.save_to_file(path, format='json')

        c2 = Config(config_path=path)
        self.assertEqual(c2.get('project_name'), 'JsonTest')
        self.assertEqual(c2.get('port'), 8520)

    def test_missing_file_raises(self):
        with self.assertRaises(ConfigError):
            Config(config_path='/tmp/does_not_exist_sfg.yaml')

    def test_invalid_yaml_raises(self):
        path = os.path.join(self.tmp_dir, 'bad.yaml')
        Path(path).write_text("project_name: Test\ndependencies:\n  - invalid: [unclosed")
        with self.assertRaises(ConfigError):
            Config(config_path=path)

    def test_invalid_json_raises(self):
        path = os.path.join(self.tmp_dir, 'bad.json')
        Path(path).write_text('{"broken":')
        with self.assertRaises(ConfigError):
            Config(config_path=path)

    def test_unsupported_format_raises(self):
        path = os.path.join(self.tmp_dir, 'config.toml')
        Path(path).write_text('[section]\nkey = "value"')
        with self.assertRaises(ConfigError):
            Config(config_path=path)


class TestConfigHelpers(unittest.TestCase):
    """Test to_dict, get_project_config, etc."""

    def test_to_dict(self):
        config = Config()
        config.load_from_dict({'project_name': 'DictTest', 'port': 8501})
        d = config.to_dict()
        self.assertIsInstance(d, dict)
        self.assertEqual(d['project_name'], 'DictTest')

    def test_get_project_config(self):
        config = Config()
        config.load_from_dict({'project_name': 'ProjCfg', 'port': 8501})
        pc = config.get_project_config()
        self.assertIn('project_name', pc)
        self.assertIn('port', pc)
        self.assertNotIn('llm', pc)

    def test_get_llm_config(self):
        config = Config()
        config.load_from_dict({'llm': {'provider': 'ollama'}})
        lc = config.get_llm_config()
        self.assertEqual(lc['provider'], 'ollama')

    def test_get_knowledge_config(self):
        config = Config()
        config.load_from_dict({})
        kc = config.get_knowledge_config()
        self.assertIsInstance(kc, dict)


if __name__ == '__main__':
    unittest.main()

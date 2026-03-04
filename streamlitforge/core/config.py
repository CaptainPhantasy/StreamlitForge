"""Configuration system for StreamlitForge."""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from ..utils.validation import validate_dict, validate_project_name


class ConfigError(Exception):
    """Base exception for configuration errors."""
    pass


class Config:
    """Configuration manager for StreamlitForge projects.

    Supports YAML and JSON configuration files with sensible defaults.
    """

    DEFAULT_CONFIG = {
        'project_name': None,
        'port': 8501,
        'venv_path': None,
        'dependencies': [],
        'streamlit_components': [],
        'features': [],
        'templates': [],
        'llm': {
            'provider': 'openrouter',
            'api_key': None,
            'model': 'llama3-70b-8192',
            'base_url': None,
            'temperature': 0.7,
            'max_tokens': 2048,
            'timeout': 30
        },
        'knowledge': {
            'streamlit_docs_url': 'https://docs.streamlit.io',
            'max_examples': 10,
            'embedding_dim': 384
            # embedding_dim validated only when > 0, any positive int accepted
        },
        'patterns': {
            'storage_dir': '.streamlitforge/patterns',
            'auto_save': True,
            'min_quality': 100
        },
        'output': {
            'project_dir': 'project',
            'verbose': False
        }
    }

    def __init__(self, config_path: Optional[str] = None, defaults: Optional[Dict] = None):
        """Initialize the configuration.

        Args:
            config_path: Path to configuration file
            defaults: Optional base configuration dictionary
        """
        self.config: Dict[str, Any] = {}

        if defaults:
            self.config.update(defaults)

        if config_path:
            self.load_from_file(config_path)

    def load_from_file(self, config_path: str) -> None:
        """Load configuration from a file.

        Args:
            config_path: Path to configuration file

        Raises:
            ConfigError: If file cannot be loaded or parsed
        """
        path = Path(config_path).expanduser().resolve()

        if not path.exists():
            raise ConfigError(f"Configuration file not found: {config_path}")

        try:
            if path.suffix in ('.yaml', '.yml'):
                import yaml
                with open(path, 'r') as f:
                    config_data = yaml.safe_load(f) or {}
            elif path.suffix == '.json':
                with open(path, 'r') as f:
                    config_data = json.load(f)
            else:
                raise ConfigError(
                    f"Unsupported configuration file format: {path.suffix}"
                )

            self._validate_and_merge(config_data)

        except ConfigError:
            raise
        except ImportError:
            raise ConfigError(
                "YAML support requires 'pyyaml' package. Install with: pip install pyyaml"
            )
        except json.JSONDecodeError as e:
            raise ConfigError(f"Invalid JSON in configuration file: {e}")
        except Exception as e:
            raise ConfigError(f"Error loading configuration: {e}")

    def load_from_dict(self, config_dict: Dict[str, Any]) -> None:
        """Load configuration from a dictionary.

        Args:
            config_dict: Configuration dictionary

        Raises:
            ConfigError: If validation fails
        """
        self._validate_and_merge(config_dict)

    def _validate_and_merge(self, config_dict: Dict[str, Any]) -> None:
        """Validate and merge configuration with defaults.

        Args:
            config_dict: Configuration dictionary to merge

        Raises:
            ConfigError: If validation fails
        """
        for key, value in config_dict.items():
            if key not in self.DEFAULT_CONFIG:
                raise ConfigError(f"Unknown configuration key: {key}")

        # Merge with defaults
        for key, default_value in self.DEFAULT_CONFIG.items():
            if key not in config_dict:
                self.config[key] = default_value
            else:
                self.config[key] = config_dict[key]

        # Validate nested configurations
        self._validate()

    def _validate(self) -> None:
        """Validate the configuration structure.

        Raises:
            ConfigError: If validation fails
        """
        # Validate port
        port = self.config.get('port')
        if port is not None:
            try:
                from ..utils.validation import validate_port
                self.config['port'] = validate_port(port)
            except (ValueError, TypeError) as e:
                raise ConfigError(f"Invalid port configuration: {e}")

        # Validate project name
        project_name = self.config.get('project_name')
        if project_name:
            try:
                from ..utils.validation import validate_project_name
                self.config['project_name'] = validate_project_name(project_name)
            except (ValueError, TypeError) as e:
                raise ConfigError(f"Invalid project name: {e}")

        # Validate LLM configuration
        llm_config = self.config.get('llm', {})
        if llm_config:
            self._validate_llm_config(llm_config)

        # Validate knowledge configuration
        knowledge_config = self.config.get('knowledge', {})
        if knowledge_config:
            self._validate_knowledge_config(knowledge_config)

    def _validate_llm_config(self, llm_config: Dict[str, Any]) -> None:
        """Validate LLM configuration.

        Args:
            llm_config: LLM configuration dictionary

        Raises:
            ConfigError: If validation fails
        """
        # Validate provider
        provider = llm_config.get('provider')
        if provider:
            valid_providers = ['openrouter', 'ollama', 'groq', 'openai', 'anthropic']
            if provider not in valid_providers:
                raise ConfigError(
                    f"Invalid LLM provider: {provider}. Must be one of {valid_providers}"
                )

        # Validate model name
        model = llm_config.get('model')
        if model and len(model) < 3:
            raise ConfigError("LLM model name is too short")

        # Validate temperature
        temperature = llm_config.get('temperature')
        if temperature is not None:
            if not (0 <= temperature <= 2):
                raise ConfigError("Temperature must be between 0 and 2")

        # Validate max tokens
        max_tokens = llm_config.get('max_tokens')
        if max_tokens is not None:
            if max_tokens < 1 or max_tokens > 32768:
                raise ConfigError("Max tokens must be between 1 and 32768")

    def _validate_knowledge_config(self, knowledge_config: Dict[str, Any]) -> None:
        """Validate knowledge base configuration.

        Args:
            knowledge_config: Knowledge configuration dictionary

        Raises:
            ConfigError: If validation fails
        """
        # Validate max examples
        max_examples = knowledge_config.get('max_examples')
        if max_examples is not None:
            if not isinstance(max_examples, int) or max_examples < 1:
                raise ConfigError("max_examples must be a positive integer")

        # Validate embedding dim
        embedding_dim = knowledge_config.get('embedding_dim')
        if embedding_dim is not None:
            if not isinstance(embedding_dim, int) or embedding_dim < 1:
                raise ConfigError("embedding_dim must be a positive integer")

    def save_to_file(self, config_path: str, format: str = 'yaml') -> None:
        """Save configuration to a file.

        Args:
            config_path: Path to save configuration to
            format: Output format ('yaml' or 'json')

        Raises:
            ConfigError: If file cannot be saved
        """
        path = Path(config_path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            if format == 'yaml':
                import yaml
                with open(path, 'w') as f:
                    yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
            elif format == 'json':
                with open(path, 'w') as f:
                    json.dump(self.config, f, indent=2)
            else:
                raise ConfigError(f"Unsupported format: {format}")

        except Exception as e:
            raise ConfigError(f"Error saving configuration: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value.

        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split('.')
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            elif not isinstance(config[k], dict):
                raise ConfigError(
                    f"Cannot set nested key '{key}': "
                    f"Intermediate key '{k}' is not a dictionary"
                )
            config = config[k]

        config[keys[-1]] = value

    def to_dict(self) -> Dict[str, Any]:
        """Get the entire configuration as a dictionary.

        Returns:
            Configuration dictionary
        """
        return dict(self.config)

    def get_project_config(self) -> Dict[str, Any]:
        """Get project-specific configuration.

        Returns:
            Project configuration dictionary
        """
        return {
            k: v for k, v in self.config.items()
            if k in ('project_name', 'port', 'venv_path', 'dependencies')
        }

    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration.

        Returns:
            LLM configuration dictionary
        """
        return self.config.get('llm', {}).copy()

    def get_knowledge_config(self) -> Dict[str, Any]:
        """Get knowledge base configuration.

        Returns:
            Knowledge configuration dictionary
        """
        return self.config.get('knowledge', {}).copy()

    def get_pattern_config(self) -> Dict[str, Any]:
        """Get pattern library configuration.

        Returns:
            Pattern configuration dictionary
        """
        return self.config.get('patterns', {}).copy()

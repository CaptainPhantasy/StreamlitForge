"""LLM Abstraction Layer and Provider Implementations."""

import requests
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ..utils.validation import validate_string, validate_bool


class LLMError(Exception):
    """Base exception for LLM errors."""
    pass


class ProviderError(LLMError):
    """Exception for provider-specific errors."""
    pass


class BaseLLMProvider(ABC):
    """Base class for LLM providers.

    All providers must implement the generate and chat methods.
    """

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate a completion from a prompt.

        Args:
            prompt: The input prompt
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated text response
        """
        pass

    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Chat with the LLM using message history.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated text response
        """
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the available model.

        Returns:
            Dictionary with model information
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available.

        Returns:
            True if provider is available, False otherwise
        """
        pass


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter LLM provider.

    Supports multiple models through OpenRouter API.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None,
                 model: str = 'llama3-70b-8192', **kwargs):
        """Initialize the OpenRouter provider.

        Args:
            api_key: OpenRouter API key
            base_url: Optional custom API endpoint
            model: Model name to use
            **kwargs: Additional parameters
        """
        self.api_key = api_key
        self.base_url = base_url or 'https://openrouter.ai/api/v1'
        self.model = model
        self._session = None

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate a completion using the completion API.

        Args:
            prompt: The input prompt
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            Generated text response
        """
        if not self._session:
            self._session = requests.Session()
            if self.api_key:
                self._session.headers.update({
                    'Authorization': f'Bearer {self.api_key}',
                    'HTTP-Referer': 'https://streamlitforge.com',
                    'X-Title': 'StreamlitForge'
                })

        payload = {
            'model': self.model,
            'prompt': prompt,
            'temperature': kwargs.get('temperature', 0.7),
            'max_tokens': kwargs.get('max_tokens', 2048)
        }

        try:
            response = self._session.post(
                f'{self.base_url}/chat/completions',
                json=payload,
                timeout=kwargs.get('timeout', 30)
            )
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except ProviderError:
            raise
        except Exception as e:
            raise ProviderError(f"OpenRouter API error: {e}")

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Chat with the model using message history.

        Args:
            messages: List of message dictionaries
            **kwargs: Additional parameters

        Returns:
            Generated text response
        """
        if not self._session:
            self._session = requests.Session()
            if self.api_key:
                self._session.headers.update({
                    'Authorization': f'Bearer {self.api_key}',
                    'HTTP-Referer': 'https://streamlitforge.com',
                    'X-Title': 'StreamlitForge'
                })

        formatted_messages = [{'role': m['role'], 'content': m['content']}
                             for m in messages]

        payload = {
            'model': self.model,
            'messages': formatted_messages,
            'temperature': kwargs.get('temperature', 0.7),
            'max_tokens': kwargs.get('max_tokens', 2048)
        }

        try:
            response = self._session.post(
                f'{self.base_url}/chat/completions',
                json=payload,
                timeout=kwargs.get('timeout', 30)
            )
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except ProviderError:
            raise
        except Exception as e:
            raise ProviderError(f"OpenRouter API error: {e}")

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information.

        Returns:
            Dictionary with model info
        """
        return {
            'provider': 'openrouter',
            'model': self.model,
            'base_url': self.base_url
        }

    def is_available(self) -> bool:
        """Check if provider is available.

        Returns:
            True if API key is configured and service is accessible
        """
        if not self.api_key:
            return False
        return True


class OllamaProvider(BaseLLMProvider):
    """Ollama local LLM provider."""

    def __init__(self, model: str = 'llama3', host: str = 'http://localhost:11434', **kwargs):
        """Initialize the Ollama provider.

        Args:
            model: Model name to use
            host: Ollama server host
            **kwargs: Additional parameters
        """
        self.model = model
        self.host = host
        self._session = None

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate a completion.

        Args:
            prompt: The input prompt
            **kwargs: Additional parameters

        Returns:
            Generated text response
        """
        if not self._session:
            self._session = requests.Session()

        payload = {
            'model': self.model,
            'prompt': prompt,
            'stream': False
        }

        try:
            response = self._session.post(
                f'{self.host}/api/generate',
                json=payload,
                timeout=kwargs.get('timeout', 120)
            )
            response.raise_for_status()
            result = response.json()
            return result.get('response', '')
        except ProviderError:
            raise
        except Exception as e:
            raise ProviderError(f"Ollama API error: {e}")

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Chat with the model.

        Args:
            messages: List of message dictionaries
            **kwargs: Additional parameters

        Returns:
            Generated text response
        """
        if not self._session:
            self._session = requests.Session()

        formatted_messages = [{'role': m['role'], 'content': m['content']}
                             for m in messages]

        payload = {
            'model': self.model,
            'messages': formatted_messages,
            'stream': False
        }

        try:
            response = self._session.post(
                f'{self.host}/api/chat',
                json=payload,
                timeout=kwargs.get('timeout', 120)
            )
            response.raise_for_status()
            result = response.json()
            return result.get('message', {}).get('content', '')
        except ProviderError:
            raise
        except Exception as e:
            raise ProviderError(f"Ollama API error: {e}")

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information.

        Returns:
            Dictionary with model info
        """
        return {
            'provider': 'ollama',
            'model': self.model,
            'host': self.host
        }

    def is_available(self) -> bool:
        """Check if provider is available.

        Returns:
            True if Ollama server is running
        """
        try:
            response = requests.get(f'{self.host}/api/tags', timeout=2)
            return response.status_code == 200
        except Exception:
            return False


class LLMRouter:
    """Router for LLM providers with fallback support.

    Provides a unified interface that automatically selects the best available provider.
    """

    def __init__(self, providers: List[BaseLLMProvider], default_provider: Optional[str] = None):
        """Initialize the LLM router.

        Args:
            providers: List of provider instances
            default_provider: Name of the default provider to use if others fail
        """
        self.providers = {p.__class__.__name__: p for p in providers}
        self.default_provider = default_provider

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate a completion.

        Tries providers in order until one succeeds.

        Args:
            prompt: The input prompt
            **kwargs: Additional parameters

        Returns:
            Generated text response

        Raises:
            LLMError: If all providers fail
        """
        last_error = None
        for name, provider in self.providers.items():
            try:
                if provider.is_available():
                    return provider.generate(prompt, **kwargs)
            except ProviderError as e:
                last_error = e
                continue

        raise LLMError(f"No LLM provider available{': ' + str(last_error) if last_error else ''}")

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Chat with the LLM.

        Tries providers in order until one succeeds.

        Args:
            messages: List of message dictionaries
            **kwargs: Additional parameters

        Returns:
            Generated text response

        Raises:
            LLMError: If all providers fail
        """
        last_error = None
        for name, provider in self.providers.items():
            try:
                if provider.is_available():
                    return provider.chat(messages, **kwargs)
            except ProviderError as e:
                last_error = e
                continue

        raise LLMError(f"No LLM provider available{': ' + str(last_error) if last_error else ''}")

    def get_provider(self, name: str) -> Optional[BaseLLMProvider]:
        """Get a specific provider by name.

        Args:
            name: Provider name

        Returns:
            Provider instance or None
        """
        return self.providers.get(name)

    def get_available_providers(self) -> List[str]:
        """Get list of available provider names.

        Returns:
            List of provider names
        """
        return [name for name, provider in self.providers.items()
                if provider.is_available()]

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about all providers.

        Returns:
            Dictionary with provider information
        """
        return {
            name: provider.get_model_info()
            for name, provider in self.providers.items()
        }

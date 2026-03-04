"""LLM Provider registry and discovery."""

from typing import Dict, List, Type

from ..base import LLMProvider


_PROVIDER_REGISTRY: Dict[str, Type[LLMProvider]] = {}


def register_provider(name: str, cls: Type[LLMProvider]):
    _PROVIDER_REGISTRY[name] = cls


def get_provider_class(name: str):
    return _PROVIDER_REGISTRY.get(name)


def list_provider_names() -> List[str]:
    return list(_PROVIDER_REGISTRY.keys())


def _register_all():
    from .ollama import OllamaProvider
    from .lmstudio import LMStudioProvider
    from .vllm import VLLMProvider
    from .localai import LocalAIProvider
    from .jan import JanProvider
    from .groq import GroqProvider
    from .openai import OpenAIProvider
    from .anthropic import AnthropicProvider
    from .google import GoogleProvider
    from .cohere import CohereProvider
    from .mistral import MistralProvider
    from .deepseek import DeepSeekProvider
    from .together import TogetherProvider
    from .replicate import ReplicateProvider
    from .openrouter import OpenRouterProvider
    from .opencode import OpenCodeGoProvider, OpenCodeZenProvider
    from .azure import AzureOpenAIProvider
    from .aws import AWSBedrockProvider
    from .pattern_library import PatternLibraryProvider

    register_provider("ollama", OllamaProvider)
    register_provider("lmstudio", LMStudioProvider)
    register_provider("vllm", VLLMProvider)
    register_provider("localai", LocalAIProvider)
    register_provider("jan", JanProvider)
    register_provider("groq", GroqProvider)
    register_provider("openai", OpenAIProvider)
    register_provider("anthropic", AnthropicProvider)
    register_provider("google", GoogleProvider)
    register_provider("cohere", CohereProvider)
    register_provider("mistral", MistralProvider)
    register_provider("deepseek", DeepSeekProvider)
    register_provider("together", TogetherProvider)
    register_provider("replicate", ReplicateProvider)
    register_provider("openrouter", OpenRouterProvider)
    register_provider("opencode_go", OpenCodeGoProvider)
    register_provider("opencode_zen", OpenCodeZenProvider)
    register_provider("azure_openai", AzureOpenAIProvider)
    register_provider("aws_bedrock", AWSBedrockProvider)
    register_provider("pattern_library", PatternLibraryProvider)


_register_all()

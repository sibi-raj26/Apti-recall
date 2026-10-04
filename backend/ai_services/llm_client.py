import os

from backend.ai_services.base import BaseLLMProvider
from backend.ai_services.providers import OllamaProvider, OpenAIProvider


class LLMClient(BaseLLMProvider):
    def __init__(self, provider: BaseLLMProvider = None):
        if provider is not None:
            self.provider = provider
            return
        provider_name = os.environ.get("AI_PROVIDER", "ollama").lower()
        if provider_name == "openai":
            self.provider = OpenAIProvider()
        else:
            self.provider = OllamaProvider()

    def structured_call(self, prompt: str, schema: dict, timeout: int = 120) -> dict:
        return self.provider.structured_call(prompt, schema, timeout=timeout)

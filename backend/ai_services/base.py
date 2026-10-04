from abc import ABC, abstractmethod


class BaseLLMProvider(ABC):
    @abstractmethod
    def structured_call(self, prompt: str, schema: dict, timeout: int = 120) -> dict:
        """Send prompt and return structured JSON response."""
        ...

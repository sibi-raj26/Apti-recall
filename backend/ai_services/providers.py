import os
import json
import requests

from backend.ai_services.base import BaseLLMProvider


class OllamaProvider(BaseLLMProvider):
    def __init__(self, base_url=None, model=None, timeout=None):
        self.base_url = base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = model or os.environ.get("OLLAMA_MODEL", "llama3.1:8b")
        self.timeout = timeout or int(os.environ.get("AI_REQUEST_TIMEOUT", 120))

    def structured_call(self, prompt: str, schema: dict, timeout: int = 120) -> dict:
        timeout = timeout or self.timeout
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
            },
            timeout=timeout,
        )
        response.raise_for_status()
        text = response.json().get("response", "{}")
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"raw": text}


class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key=None, model=None, timeout=None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model = model or "gpt-4o-mini"
        self.timeout = timeout or int(os.environ.get("AI_REQUEST_TIMEOUT", 120))

    def structured_call(self, prompt: str, schema: dict, timeout: int = 120) -> dict:
        if not self.api_key:
            raise RuntimeError("OpenAI API key is not configured.")
        timeout = timeout or self.timeout
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_schema", "json_schema": {"name": "response", "schema": schema}},
        }
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return json.loads(content)


class MockLLMProvider(BaseLLMProvider):
    def __init__(self, responses=None):
        self.responses = responses or []
        self.call_index = 0

    def structured_call(self, prompt: str, schema: dict, timeout: int = 120) -> dict:
        if self.call_index < len(self.responses):
            resp = self.responses[self.call_index]
            self.call_index += 1
            return resp
        raise RuntimeError("No more mock LLM responses configured.")

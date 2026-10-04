import json

from backend.ai_services.llm_client import LLMClient

llm_client = LLMClient()


def generate_structured(prompt: str, schema: dict, llm_client_instance=None, timeout: int = 120) -> dict:
    client = llm_client_instance or llm_client
    return client.structured_call(prompt, schema, timeout=timeout)

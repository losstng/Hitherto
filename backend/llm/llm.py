import os
import requests
from typing import List, Dict, Any, Optional

# Endpoint/local model config
LLM_HTTP_BASE = os.getenv("LOCAL_LLM_HTTP_BASE", "http://127.0.0.1:1234/v1")
LLM_CHAT_COMPLETIONS = f"{LLM_HTTP_BASE}/chat/completions"
LLM_MODEL = os.getenv("LOCAL_LLM_MODEL", "openai/gpt-oss-20b")

class LocalLLMClient:
    """
    Simple client for local OpenAI-compatible LLM HTTP endpoint
    (e.g. LM Studio, Open WebUI, etc.).
    """
    def __init__(self, model: Optional[str] = None):
        self.model = model or LLM_MODEL

    def complete_chat(self, messages: List[Dict[str, str]], max_tokens: int = 512, temperature: float = 0.7) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False
        }
        try:
            resp = requests.post(LLM_CHAT_COMPLETIONS, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "[No LLM reply]")
        except Exception as e:
            return f"[LLM HTTP error: {e}]"


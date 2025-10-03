import os
import json
from typing import List, Optional, Union, Dict, Any
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class LLMClient:
    """Minimal OpenRouter client for chat-style LLM completions."""

    DEFAULT_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(
        self,
        api_key_env: str = "OPENROUTER_API_KEY",
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        default_model: str = "meta-llama/llama-3.3-8b-instruct:free",
    ):
        self.api_key = api_key or os.environ.get(api_key_env)
        if not self.api_key:
            raise RuntimeError(f"OpenRouter API key missing (check .env for {api_key_env}).")

        self.endpoint = endpoint or self.DEFAULT_ENDPOINT
        self.default_model = default_model

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
        )

    def _build_messages(
        self,
        system: Optional[Union[str, List[str]]],
        user: Union[str, List[str]],
        extra: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        messages: List[Dict[str, Any]] = []
        if system:
            if isinstance(system, list):
                for s in system:
                    messages.append({"role": "system", "content": s})
            else:
                messages.append({"role": "system", "content": system})

        if isinstance(user, list):
            for u in user:
                messages.append({"role": "user", "content": u})
        else:
            messages.append({"role": "user", "content": user})

        if extra:
            messages.extend(extra)
        return messages

    def chat(
        self,
        system: Optional[Union[str, List[str]]] = None,
        user: Union[str, List[str]] = "",
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 512,
        stop: Optional[List[str]] = None,
        extra_messages: Optional[List[Dict[str, Any]]] = None,
        raw_response: bool = False,
    ) -> Union[str, Dict[str, Any]]:
        model_to_use = model or self.default_model
        payload = {
            "model": model_to_use,
            "messages": self._build_messages(system, user, extra_messages),
            "temperature": float(temperature),
            "max_tokens": int(max_tokens),
        }
        if stop:
            payload["stop"] = stop

        resp = self.session.post(self.endpoint, data=json.dumps(payload), timeout=60)
        try:
            resp.raise_for_status()
        except requests.HTTPError as e:
            raise RuntimeError(f"OpenRouter API error: {e}, response: {resp.text}")

        data = resp.json()
        if raw_response:
            return data

        try:
            choices = data.get("choices") or []
            if not choices:
                if "output" in data:
                    return data["output"]
                raise RuntimeError(f"Unexpected response shape: {data}")

            contents = []
            for ch in choices:
                msg = ch.get("message") or {}
                content = msg.get("content")
                contents.append(content or "")
            return "\n".join(contents).strip()
        except Exception as e:
            raise RuntimeError(f"Failed to parse OpenRouter response: {e}; raw: {data}")

# Convenience helper
def get_llm_client(**kwargs) -> LLMClient:
    return LLMClient(**kwargs)
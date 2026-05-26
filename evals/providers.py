"""Provider boundary for generation and future evaluator/judge calls."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Generator, Protocol
import requests

from .config import get_config_value
from .queue import LLMQueue, get_shared_llm_queue


class LLMProvider(Protocol):
    name: str
    model: str | None

    def generate(self, prompt: str) -> dict:
        ...

    def stream(self, prompt: str) -> Generator[str, None, None]:
        ...


@dataclass
class OllamaProvider:
    model: str | None = None
    timeout_seconds: int = 120
    num_ctx: int = 4096
    queue: LLMQueue | None = None

    name: str = "ollama"

    def __post_init__(self) -> None:
        from summarizer.ollama_client import OllamaSummarizer

        self.queue = self.queue or LLMQueue(1)
        self.summarizer = OllamaSummarizer(
            model=self.model,
            timeout=self.timeout_seconds,
            num_ctx=self.num_ctx,
        )
        self.model = self.summarizer.model

    def generate(self, prompt: str) -> dict:
        return self.queue.run(self.summarizer._generate_response, prompt)

    def stream(self, prompt: str) -> Generator[str, None, None]:
        # Keep the queue slot for the full streaming response.
        with self.queue.slot():
            yield from self.summarizer._stream_response(prompt)


@dataclass
class GeminiProvider:
    model: str
    api_key_env: str = "GEMINI_API_KEY"
    queue: LLMQueue | None = None

    name: str = "gemini"

    def __post_init__(self) -> None:
        self.queue = self.queue or LLMQueue(1)

    @property
    def available(self) -> bool:
        return bool(os.getenv(self.api_key_env))

    def generate(self, prompt: str) -> dict:
        if not self.available:
            return {
                "summary": "",
                "error": f"{self.api_key_env} is not configured",
                "success": False,
            }

        def _call_gemini() -> dict:
            api_key = os.getenv(self.api_key_env)
            url = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"{self.model}:generateContent"
            )
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": prompt}],
                    }
                ],
                "generationConfig": {
                    "temperature": 0.0,
                    "responseMimeType": "application/json",
                },
            }
            response = requests.post(
                url,
                headers={"x-goog-api-key": api_key or ""},
                json=payload,
                timeout=90,
            )
            if not response.ok:
                return {
                    "summary": "",
                    "model": self.model,
                    "error": (
                        "Gemini request failed "
                        f"with HTTP {response.status_code}: {response.reason}"
                    ),
                    "success": False,
                }
            data = response.json()
            text = ""
            for candidate in data.get("candidates", []):
                parts = candidate.get("content", {}).get("parts", [])
                for part in parts:
                    text += part.get("text", "")
            if not text:
                raise RuntimeError("Gemini returned an empty response")
            return {
                "summary": text,
                "model": self.model,
                "success": True,
            }

        try:
            result = self.queue.run(_call_gemini)
            if result.get("success") is False:
                return result
            return result
        except Exception as exc:
            return {
                "summary": "",
                "model": self.model,
                "error": f"{type(exc).__name__}: Gemini judge call failed",
                "success": False,
            }

    def stream(self, prompt: str) -> Generator[str, None, None]:
        result = self.generate(prompt)
        if result.get("success"):
            yield result.get("summary", "")
        else:
            yield f"Error: {result.get('error', 'Gemini provider unavailable')}"


@dataclass
class OpenRouterProvider:
    model: str
    api_key_env: str = "OPENROUTER_API_KEY"
    base_url: str = "https://openrouter.ai/api/v1"
    site_url: str | None = None
    app_name: str | None = None
    timeout_seconds: int = 90
    queue: LLMQueue | None = None

    name: str = "openrouter"

    def __post_init__(self) -> None:
        self.queue = self.queue or LLMQueue(1)
        self.base_url = self.base_url.rstrip("/")

    @property
    def available(self) -> bool:
        return bool(os.getenv(self.api_key_env))

    def _headers(self) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {os.getenv(self.api_key_env) or ''}",
            "Content-Type": "application/json",
        }
        if self.site_url:
            headers["HTTP-Referer"] = self.site_url
        if self.app_name:
            headers["X-Title"] = self.app_name
        return headers

    def generate(self, prompt: str) -> dict:
        if not self.available:
            return {
                "summary": "",
                "error": f"{self.api_key_env} is not configured",
                "success": False,
            }

        def _call_openrouter() -> dict:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0,
                },
                timeout=self.timeout_seconds,
            )
            if not response.ok:
                return {
                    "summary": "",
                    "model": self.model,
                    "error": (
                        "OpenRouter request failed "
                        f"with HTTP {response.status_code}: {response.reason}"
                    ),
                    "success": False,
                }

            data = response.json()
            choices = data.get("choices") or []
            if not choices:
                raise RuntimeError("OpenRouter returned no choices")

            message = choices[0].get("message") or {}
            text = message.get("content") or choices[0].get("text") or ""
            if not text:
                raise RuntimeError("OpenRouter returned an empty response")

            return {
                "summary": text,
                "model": self.model,
                "success": True,
            }

        try:
            result = self.queue.run(_call_openrouter)
            if result.get("success") is False:
                return result
            return result
        except Exception as exc:
            return {
                "summary": "",
                "model": self.model,
                "error": f"{type(exc).__name__}: OpenRouter call failed",
                "success": False,
            }

    def stream(self, prompt: str) -> Generator[str, None, None]:
        result = self.generate(prompt)
        if result.get("success"):
            yield result.get("summary", "")
        else:
            yield f"Error: {result.get('error', 'OpenRouter provider unavailable')}"


def build_llm_queue(config: dict, section: str = "llm.generator") -> LLMQueue:
    max_concurrency = get_config_value(config, f"{section}.max_concurrency", 1)
    provider_name = get_config_value(config, f"{section}.provider", "ollama")
    return get_shared_llm_queue(
        name=str(provider_name),
        max_concurrency=max_concurrency,
    )


def build_generator_provider(
    config: dict,
    selected_model: str | None = None,
    num_ctx: int = 4096,
) -> LLMProvider:
    provider_name = get_config_value(config, "llm.generator.provider", "ollama")
    timeout = int(get_config_value(config, "llm.generator.timeout_seconds", 120))
    queue = build_llm_queue(config)

    if provider_name != "ollama":
        if provider_name == "openrouter":
            return OpenRouterProvider(
                model=get_config_value(config, "llm.openrouter.model", selected_model or ""),
                api_key_env=get_config_value(config, "llm.openrouter.api_key_env", "OPENROUTER_API_KEY"),
                base_url=get_config_value(config, "llm.openrouter.base_url", "https://openrouter.ai/api/v1"),
                site_url=get_config_value(config, "llm.openrouter.site_url"),
                app_name=get_config_value(config, "llm.openrouter.app_name", "summary"),
                timeout_seconds=timeout,
                queue=queue,
            )
        raise ValueError(f"Unsupported generation provider: {provider_name}")

    return OllamaProvider(
        model=selected_model,
        timeout_seconds=timeout,
        num_ctx=num_ctx,
        queue=queue,
    )


def build_optional_judge_provider(config: dict) -> LLMProvider | None:
    judge_provider = get_config_value(config, "eval.deepeval.judge.provider", "gemini")
    if judge_provider == "gemini":
        if not get_config_value(config, "eval.deepeval.judge.allow_external", False):
            return None
        return GeminiProvider(
            model=get_config_value(config, "eval.deepeval.judge.model", "gemini-2.0-flash"),
            api_key_env=get_config_value(config, "llm.gemini.api_key_env", "GEMINI_API_KEY"),
            queue=build_llm_queue(config),
        )

    if judge_provider == "openrouter":
        if not get_config_value(config, "eval.deepeval.judge.allow_external", False):
            return None
        return OpenRouterProvider(
            model=get_config_value(config, "eval.deepeval.judge.model", None)
            or get_config_value(config, "llm.openrouter.model", "openai/gpt-4.1-nano"),
            api_key_env=get_config_value(config, "llm.openrouter.api_key_env", "OPENROUTER_API_KEY"),
            base_url=get_config_value(config, "llm.openrouter.base_url", "https://openrouter.ai/api/v1"),
            site_url=get_config_value(config, "llm.openrouter.site_url"),
            app_name=get_config_value(config, "llm.openrouter.app_name", "summary"),
            queue=build_llm_queue(config),
        )

    if judge_provider == "ollama":
        return OllamaProvider(queue=build_llm_queue(config))

    return None

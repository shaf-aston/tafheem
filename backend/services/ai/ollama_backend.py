"""Ollama local LLM backend, no API key, runs 100 % offline.

Requires:
  1. Install Ollama: https://ollama.com
  2. Pull a model:   ollama pull qwen2.5:3b   (≈ 2 GB, fast on CPU)
     Alternatives:   ollama pull qwen2.5:7b   (better Arabic, needs more RAM)
                     ollama pull aya:8b        (multilingual-first)

The backend is probed once on first use; if Ollama isn't running it silently
returns is_available() = False so the caller can fall back to local-only mode.
"""
from __future__ import annotations

import logging

import httpx

from backend.config import get_settings
from backend.services.ai.base import AIBackend

logger = logging.getLogger(__name__)

_CONNECT_TIMEOUT = 3.0    # seconds, quick probe; Ollama is local
_REQUEST_TIMEOUT = 120.0  # seconds, generation can take a while on CPU


class OllamaBackend(AIBackend):
    """HTTP client for Ollama's /api/chat endpoint."""

    def __init__(self) -> None:
        self._available: bool | None = None  # None = not yet probed

    def name(self) -> str:
        cfg = get_settings()
        return f"ollama ({cfg.ollama_model} @ {cfg.ollama_url})"

    def is_available(self) -> bool:
        if self.retired_reason:
            return False
        if self._available is None:
            self._probe()
        return bool(self._available)

    def _probe(self) -> None:
        """Check whether the Ollama server is reachable."""
        try:
            url = get_settings().ollama_url.rstrip("/")
            httpx.get(f"{url}/api/tags", timeout=_CONNECT_TIMEOUT)
            self._available = True
            logger.info("Ollama server found at %s", url)
        except Exception as exc:
            self._available = False
            logger.info("Ollama not available (%s), local-only mode", exc)

    def complete_json(self, messages: list[dict], max_tokens: int) -> dict:
        cfg = get_settings()
        url = cfg.ollama_url.rstrip("/") + "/api/chat"

        payload = {
            "model": cfg.ollama_model,
            "messages": messages,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": cfg.ai_temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            resp = httpx.post(url, json=payload, timeout=_REQUEST_TIMEOUT)
            resp.raise_for_status()
        except httpx.ConnectError as exc:
            self._available = False
            raise TimeoutError("Ollama server not reachable") from exc
        except httpx.TimeoutException as exc:
            raise TimeoutError("Ollama request timed out") from exc

        data = resp.json()
        if content := data.get("message", {}).get("content", ""):
            return self.parse_json(content)
        else:
            raise ValueError("Ollama returned an empty response")


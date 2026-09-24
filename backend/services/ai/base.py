"""Abstract AI backend interface."""
from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod

from backend.services.fallback import Retirable


class AIBackend(Retirable, ABC):
    """Common interface all AI backends must implement.

    `retired_reason` and `retire()` come from Retirable, which the ears share:
    striking off an engine that will never answer is the same idea on both
    sides, so it is written once (services/fallback).
    """

    @abstractmethod
    def complete_json(self, messages: list[dict], max_tokens: int) -> dict:
        """Send a chat completion and return parsed JSON dict."""

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the backend can handle requests right now."""

    @abstractmethod
    def name(self) -> str:
        """Human-readable backend name for logging / health endpoint."""

    @staticmethod
    def parse_json(raw: str) -> dict:
        """Model output to dict: fences off, then the outermost {...} if it chatted."""
        cleaned = re.sub(r"^```(?:json)?\n?", "", raw.strip())
        cleaned = re.sub(r"\n?```$", "", cleaned)
        if match := re.search(r"\{.*\}", cleaned, re.DOTALL):
            cleaned = match[0]
        return json.loads(cleaned)

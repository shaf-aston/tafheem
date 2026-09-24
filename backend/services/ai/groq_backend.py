"""Groq cloud AI backend."""
from __future__ import annotations

import logging
import time
from typing import Callable, TypeVar

from backend.config import get_settings
from backend.services.ai.base import AIBackend

logger = logging.getLogger(__name__)

T = TypeVar("T")

_RETRIABLE_STATUS = {429, 500, 502, 503, 504}
_AUTH_FAILURE_STATUS = {401, 403}


class GroqBackend(AIBackend):
    """Thin wrapper around the Groq Python SDK."""

    def __init__(self) -> None:
        self._client = None

    def name(self) -> str:
        return f"groq ({get_settings().groq_model})"

    def is_available(self) -> bool:
        return get_settings().has_groq and not self.retired_reason

    def _get_client(self):
        if self._client is None:
            from groq import Groq  # lazy import, groq SDK is optional
            api_key = get_settings().groq_api_key
            if not api_key.strip():
                raise ValueError("GROQ_API_KEY not configured")
            # max_retries=0: the SDK would otherwise retry inside our retry,
            # honouring Groq's "try again in 29s" each time, unseen and unbounded.
            self._client = Groq(api_key=api_key, max_retries=0,
                                timeout=get_settings().groq_timeout_seconds)
        return self._client

    def complete_json(self, messages: list[dict], max_tokens: int) -> dict:
        raw = self._retry(lambda: self._raw_complete(messages, max_tokens))
        return self.parse_json(raw)

    def _raw_complete(self, messages: list[dict], max_tokens: int) -> str:
        from groq._exceptions import APIConnectionError, APIError, APITimeoutError  # noqa: F401
        settings = get_settings()
        extra = {}
        # A reasoning model thinks and answers out of one token budget. Left at
        # its default it spends the budget thinking and the answer comes back
        # empty, which is how gpt-oss first arrived here; an empty reply, not
        # an error. Not every model takes the setting, so it is only sent when
        # config asks for one.
        if effort := settings.groq_reasoning_effort.strip():
            extra["reasoning_effort"] = effort
        response = self._get_client().chat.completions.create(
            model=settings.groq_model,
            messages=messages,
            temperature=settings.ai_temperature,
            max_tokens=max_tokens,
            # Asked for outright rather than hoped for: every prompt here ends
            # by describing the JSON object it wants, and this method's one
            # caller is named complete_json.
            response_format={"type": "json_object"},
            **extra,
        )
        if content := response.choices[0].message.content:
            return content
        raise ValueError("Groq answered with nothing at all, the model may have spent "
                         "its whole token budget reasoning. Raise max_tokens or lower "
                         "GROQ_REASONING_EFFORT.")

    def _retry(self, func: Callable[[], T], max_retries: int = 2, base_delay: float = 1.0) -> T:
        from groq._exceptions import APIConnectionError, APIError, APITimeoutError

        for attempt in range(max_retries + 1):
            try:
                return func()
            except (APIConnectionError, APITimeoutError) as exc:
                if attempt == max_retries:
                    raise TimeoutError(
                        f"Groq unavailable after {max_retries + 1} attempts"
                    ) from exc
                self._backoff(attempt, base_delay, exc)
            except APIError as exc:
                if self._is_auth(exc):
                    # The status is carried over by hand, and the SDK's own error
                    # is left behind on purpose. Two reasons, and both matter:
                    # services/fallback strikes a backend off by the status on
                    # the error, so a plain ValueError meant a rejected key was
                    # retried on every request for the life of the run; and the
                    # SDK's error holds the request that made it, headers and
                    # all, which is the API key. Nothing logs it today, and
                    # nothing should be able to start.
                    refused = ValueError("Invalid or expired GROQ_API_KEY")
                    refused.status_code = getattr(exc, "status_code", None) or 401
                    raise refused from None
                if attempt < max_retries and self._is_retriable(exc):
                    self._backoff(attempt, base_delay, exc)
                    continue
                raise
        raise RuntimeError("unreachable")

    @staticmethod
    def _backoff(attempt: int, base: float, exc: Exception) -> None:
        delay = base * (2 ** attempt)
        logger.warning("Groq error (attempt %d), retry in %.1fs: %s", attempt + 1, delay, exc)
        time.sleep(delay)

    @staticmethod
    def _is_auth(exc) -> bool:
        status = getattr(exc, "status_code", None)
        msg = str(exc).lower()
        return status in _AUTH_FAILURE_STATUS or "unauthorized" in msg or "invalid api key" in msg

    @staticmethod
    def _is_retriable(exc) -> bool:
        status = getattr(exc, "status_code", None)
        return status in _RETRIABLE_STATUS or "rate limit" in str(exc).lower()


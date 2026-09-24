"""AI backend registry and high-level grammar analyzers.

Backend resolution order (auto mode):
  1. Groq: if GROQ_API_KEY is set
  2. Ollama, if Ollama server is reachable on localhost
  3. None: local rule engine + morphology only

Public functions mirror the old groq/__init__.py interface so routers
need no changes:
    analyze_iraab, analyze_sarf,
    generate_practice, load_nahw_rules, get_backend_name
"""
from __future__ import annotations

import logging
import threading
from functools import lru_cache

from backend.config import get_settings
from backend.services.ai import prompts
from backend.services.ai.base import AIBackend
from backend.services.ai.groq_backend import GroqBackend
from backend.services.ai.ollama_backend import OllamaBackend
from backend.services.fallback import permanent_failure

logger = logging.getLogger(__name__)

# Singletons, created once, reused across requests
_groq = GroqBackend()
_ollama = OllamaBackend()


def _get_backend() -> AIBackend | None:
    """Return the active backend, or None if running in local-only mode."""
    mode = get_settings().effective_backend

    if mode == "groq":
        if _groq.is_available():
            return _groq
        logger.warning(
            "Groq unusable, %s. Running on the local rule engine.",
            _groq.retired_reason or "GROQ_API_KEY is missing",
        )
        return None

    if mode == "ollama":
        if _ollama.is_available():
            return _ollama
        logger.warning(
            "Ollama unusable, %s. Running on the local rule engine.",
            _ollama.retired_reason or "the server is not reachable",
        )
        return None

    if mode == "none":
        return None

    # mode == "auto": try Groq first, then Ollama
    if _groq.is_available():
        return _groq
    return _ollama if _ollama.is_available() else None


def is_ai_available() -> bool:
    """True when an AI backend is configured and reachable.

    Routers must use this, never string-compare get_backend_name(),
    which is display-only and free to change wording.
    """
    return _get_backend() is not None


def get_backend_name() -> str:
    """Return a human-readable description of the active AI backend (display only)."""
    b = _get_backend()
    return b.name() if b else "none (local rule engine only)"


def _ask(user_prompt: str, max_tokens: int) -> dict:
    """Call the active AI backend; raises RuntimeError when none is available."""
    backend = _get_backend()
    if backend is None:
        raise RuntimeError(
            "No AI backend available. Set GROQ_API_KEY in .env, or install Ollama "
            "(https://ollama.com) and run: ollama pull qwen2.5:3b"
        )
    try:
        return backend.complete_json(
            messages=[
                {"role": "system", "content": prompts.system_prompt()},
                {"role": "user",   "content": user_prompt},
            ],
            max_tokens=max_tokens,
        )
    except Exception as exc:
        if reason := permanent_failure(exc):
            backend.retire(reason)
            logger.warning("Retiring %s for this run, %s", backend.name(), reason)
        raise


# ── High-level analyzers ──────────────────────────────────────────────────────

# One I'raab at a time, and each answer kept. The page fires the same
# sentence twice on arrival (React StrictMode) and again on every reload; run
# in parallel both pay Groq, and the free tier's 8,000 tokens a minute is
# spent by the fourth call. Serialised, the second finds the first's answer.
# A failed call is not kept (lru_cache stores results, never exceptions).
_iraab_turn = threading.Lock()


@lru_cache(maxsize=get_settings().ai_answer_cache_size)
def _iraab(sentence: str, morpho_tags: str) -> dict:
    return _ask(
        prompts.IRAAB_USER.format(sentence=sentence, qalsadi_tags=morpho_tags or "Not available"),
        max_tokens=get_settings().iraab_max_tokens,
    )


def analyze_iraab(sentence: str, morpho_tags: str) -> dict:
    """Full proof-based I'raab analysis of an Arabic sentence."""
    with _iraab_turn:
        return _iraab(sentence, morpho_tags)


def analyze_sarf(word: str, morpho_tags: str) -> dict:
    """Sarf (morphology) analysis of a single Arabic word."""
    return _ask(
        prompts.SARF_USER.format(word=word, qalsadi_tags=morpho_tags or "Not available"),
        max_tokens=get_settings().sarf_max_tokens,
    )


def generate_practice(sentence: str, iraab_summary: str) -> dict:
    """Generate 4 practice questions for a sentence's I'raab."""
    settings = get_settings()
    return _ask(
        prompts.PRACTICE_USER.format(
            sentence=sentence,
            iraab_summary=iraab_summary[: settings.iraab_summary_truncate_chars],
        ),
        max_tokens=settings.practice_max_tokens,
    )


def explain_root_entry(root: str, entry: str) -> dict:
    """A Maqayees entry retold in plain English.

    The Arabic handed over is the app's own copy of the book, never anything a
    reader typed, so nothing a reader writes reaches the model through here.
    """
    settings = get_settings()
    return _ask(
        prompts.ROOT_ENTRY_USER.format(
            root=root,
            entry=entry[: settings.root_entry_truncate_chars],
        ),
        max_tokens=settings.root_entry_max_tokens,
    )


def explain_root_entry_lines(root: str, lines: list[str]) -> dict:
    """A Maqayees entry put into English line by line, keeping the numbering.

    The caller owns the split and the count check: this hands the lines over
    numbered and returns whatever came back, and the router refuses an answer
    whose count does not match rather than showing English under the wrong
    Arabic. The Arabic is the app's own copy of the book, never reader input.
    """
    numbered = "\n".join(f"{i + 1}. {line}" for i, line in enumerate(lines))
    return _ask(
        prompts.ROOT_ENTRY_LINES_USER.format(root=root, numbered=numbered, count=len(lines)),
        max_tokens=get_settings().root_entry_max_tokens,
    )


# ── Re-export for main.py startup ─────────────────────────────────────────────
load_nahw_rules = prompts.load_nahw_rules

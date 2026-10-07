"""AI backend registry and high-level grammar analyzers.

Backend resolution order (auto mode):
  1. Groq: if GROQ_API_KEY is set
  2. Ollama, if Ollama server is reachable on localhost
  3. None: local rule engine + morphology only

Public functions mirror the old groq/__init__.py interface so routers
need no changes:
    analyze_sarf, explain_root_entry, explain_root_entry_lines, get_backend_name
"""
from __future__ import annotations

import logging

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

def analyze_sarf(word: str, morpho_tags: str) -> dict:
    """Sarf (morphology) analysis of a single Arabic word."""
    return _ask(
        prompts.SARF_USER.format(word=word, qalsadi_tags=morpho_tags or "Not available"),
        max_tokens=get_settings().sarf_max_tokens,
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


def translate_sentence(text: str, word_by_word: str) -> dict:
    """A reader's phrase or sentence in natural English, steered by its word-by-word.

    Unlike the two below, this hands the model what a reader typed. The route
    caps its length, and the answer only ever goes back to that reader as text.
    """
    return _ask(
        prompts.SENTENCE_USER.format(text=text, word_by_word=word_by_word),
        max_tokens=get_settings().sentence_max_tokens,
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



def checked_sentence(words: list[str], passes) -> dict | None:
    """One short sentence from `words` that `passes` accepts, or None.

    The model only writes; `passes` is a plain program that checks every word,
    so nothing it made up reaches the learner. Up to sentence_max_tries tries.
    """
    settings = get_settings()
    prompt = prompts.CHECKED_SENTENCE_USER.format(words="، ".join(words))
    for _ in range(settings.sentence_max_tries):
        try:
            reply = _ask(prompt, max_tokens=settings.sentence_max_tokens)
        except Exception as exc:  # a failed call is a failed try, not a crash
            logger.warning("checked sentence try failed: %r", exc)
            continue
        ar, en = str(reply.get("ar", "")).strip(), str(reply.get("en", "")).strip()
        if ar and en and passes(ar):
            return {"ar": ar, "en": en}
    return None

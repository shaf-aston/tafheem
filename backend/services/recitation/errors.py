"""What the ears raise, and the one lock they share. Here so no ear imports another."""
from __future__ import annotations

import threading


class Unreadable(RuntimeError):
    """The recording itself cannot be decoded, so no ear will ever read it.

    Not an engine failing: falling through to the next one only spends another
    few seconds reaching the same answer. It has happened, from a truncated
    browser recording that carried a valid webm header and nothing playable
    behind it, and it reached the reader as "Could not make that out", which
    blames the listening for something the recording did.
    """


class NotInstalled(RuntimeError):
    """The engine is not available on this machine. Said plainly, not guessed at."""


# Held around every local model call (whisper and letters, never nested): a search
# skips routers/listen.py's _turn, and two calls at once fight for the cores.
local_lock = threading.Lock()

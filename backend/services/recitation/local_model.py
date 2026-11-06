"""An onnx ear kept on this machine: loaded on first use and kept, run under the shared lock and timed.

letters.py and sounds.py each say which files they need and what to do with the
output; the loading, the failure and the lock are here once.
"""
from __future__ import annotations

import logging
import time
from typing import Callable

from backend.config import data_path, get_settings
from backend.services.core.timing import timed
from backend.services.recitation.errors import NotInstalled, local_lock

log = logging.getLogger(__name__)


class LocalModel:
    """`read(folder)` loads what the model needs beside it (its vocabulary, say) and is kept as `extra`."""

    def __init__(self, name: str, folder_key: str, file: str, read: Callable = lambda folder: None):
        self.name, self._folder_key, self._file, self._read = name, folder_key, file, read
        self._loaded: tuple | None = None

    @property
    def extra(self):
        return self.load()[1]

    def installed(self) -> bool:
        """The model file is here. Whether it loads is found out on first use."""
        return (data_path(self._folder_key) / self._file).is_file()

    def load(self) -> tuple:
        """(session, extra), loaded on first use and kept. NotInstalled when it cannot be."""
        if self._loaded is not None:
            return self._loaded
        folder = data_path(self._folder_key)
        try:
            import onnxruntime as ort
            extra = self._read(folder)
            started = time.perf_counter()
            options = ort.SessionOptions()
            options.intra_op_num_threads = get_settings().recitation_threads
            session = ort.InferenceSession(str(folder / self._file), options, providers=["CPUExecutionProvider"])
        except Exception as exc:
            raise NotInstalled(f"the {self.name} model could not be loaded from {folder}: {exc}") from exc
        self._loaded = (session, extra)
        log.info("loaded  model=%s  threads=%d  %.0fms", self.name, options.intra_op_num_threads,
                 (time.perf_counter() - started) * 1000)
        return self._loaded

    def run(self, what: str, feed: dict, **fields):
        """The model's outputs for `feed`, one at a time with the other local models: they share the cores."""
        session = self.load()[0]
        with local_lock:
            return timed(what, session.run, None, feed, **fields)

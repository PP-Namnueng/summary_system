"""Concurrency boundary for local and external LLM calls."""

from __future__ import annotations

from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
from threading import BoundedSemaphore
from typing import Callable, Iterator, TypeVar


T = TypeVar("T")
_SHARED_QUEUES: dict[tuple[str, int], "LLMQueue"] = {}


class LLMQueue:
    """Small synchronous queue for provider calls.

    Ollama defaults to a single local worker. External providers can opt into a
    larger value through config without changing evaluator or retriever code.
    """

    def __init__(self, max_concurrency: int = 1):
        self.max_concurrency = max(1, int(max_concurrency or 1))
        self._semaphore = BoundedSemaphore(self.max_concurrency)
        self._executor = ThreadPoolExecutor(max_workers=self.max_concurrency)

    def run(self, func: Callable[..., T], *args, **kwargs) -> T:
        with self._semaphore:
            return func(*args, **kwargs)

    def submit(self, func: Callable[..., T], *args, **kwargs):
        return self._executor.submit(self.run, func, *args, **kwargs)

    @contextmanager
    def slot(self) -> Iterator[None]:
        """Hold one queue slot for a streaming provider call."""
        with self._semaphore:
            yield


def get_shared_llm_queue(name: str = "ollama", max_concurrency: int = 1) -> LLMQueue:
    """Return a process-local queue shared by Streamlit runtime LLM calls."""
    normalized_concurrency = max(1, int(max_concurrency or 1))
    key = (name, normalized_concurrency)
    if key not in _SHARED_QUEUES:
        _SHARED_QUEUES[key] = LLMQueue(normalized_concurrency)
    return _SHARED_QUEUES[key]

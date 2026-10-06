"""Base agent classes, communication protocol, and exceptions for Multi-Agent Coordinator."""

import asyncio
import logging
from typing import Any, Dict, List, Optional


def get_logger(name: str = "coordinator") -> logging.Logger:
    """Return a configured logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


class CoordinatorException(Exception):
    """Exception raised by Coordinator when error budget or retries are exhausted."""
    pass


class WorkerError(Exception):
    """Exception raised by a worker agent during task execution."""
    pass


class MessageQueue:
    """Simple in-memory message queue for coordinator-worker communication."""

    def __init__(self) -> None:
        self.queue: List[Dict[str, Any]] = []

    def push(self, message: Dict[str, Any]) -> None:
        self.queue.append(message)

    def pop(self) -> Optional[Dict[str, Any]]:
        return self.queue.pop(0) if self.queue else None

    def get_all(self) -> List[Dict[str, Any]]:
        return list(self.queue)

    def is_empty(self) -> bool:
        return len(self.queue) == 0

    def __len__(self) -> int:
        return len(self.queue)

    def __bool__(self) -> bool:
        return True


class BaseAgent:
    """Base class for worker agents."""

    def __init__(self, name: str, description: str = "") -> None:
        self.name = name
        self.description = description
        self.logger = get_logger(name)

    async def process_async(self, content: Any) -> Dict[str, Any]:
        """Asynchronously process content and return a standardized result dictionary."""
        raise NotImplementedError("Subclasses must implement process_async")

    def process(self, content: Any) -> Dict[str, Any]:
        """Synchronous wrapper for process_async."""
        return asyncio.run(self.process_async(content))


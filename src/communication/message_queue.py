"""Async message queue implementation for Multi-Agent Communication."""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid


class MessageQueue:
    """Async in-memory message queue for agent communication."""

    def __init__(self) -> None:
        self.queues: Dict[str, asyncio.Queue] = {}
        self.message_log: List[Dict[str, Any]] = []

    def __bool__(self) -> bool:
        return True

    def register_agent(self, agent_name: str) -> None:
        """Register an agent to receive messages."""
        self.queues[agent_name] = asyncio.Queue()

    async def send_message(self, from_agent: str, to_agent: str, message: Dict[str, Any]) -> str:
        """Send message from one agent to another."""
        if to_agent not in self.queues:
            raise ValueError(f"Agent {to_agent} not registered")

        # Add metadata
        message["from"] = from_agent
        message["to"] = to_agent
        message["timestamp"] = datetime.now().isoformat()
        message["id"] = str(uuid.uuid4())

        # Log message
        self.message_log.append(message)

        # Enqueue
        await self.queues[to_agent].put(message)

        return message["id"]

    async def receive_message(self, agent_name: str, timeout: float = 30.0) -> Dict[str, Any]:
        """Receive next message for an agent."""
        if agent_name not in self.queues:
            raise ValueError(f"Agent {agent_name} not registered")

        try:
            message = await asyncio.wait_for(
                self.queues[agent_name].get(),
                timeout=timeout,
            )
            return message
        except (asyncio.TimeoutError, TimeoutError):
            raise TimeoutError(f"No message for {agent_name} within {timeout}s")

    def get_message_log(self, agent_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get message history."""
        if agent_name:
            return [m for m in self.message_log if m.get("from") == agent_name or m.get("to") == agent_name]
        return list(self.message_log)


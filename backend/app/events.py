"""Event bus for WebSocket fan-out during test execution and generation.

Subscribers register per execution/generation ID and receive
typed events via asyncio.Queue.
"""

import asyncio
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Event type identifiers."""
    # Execution events
    EXECUTION_STARTED = "execution_started"
    EXECUTION_COMPLETED = "execution_completed"
    EXECUTION_CANCELLED = "execution_cancelled"
    TEST_STARTED = "test_started"
    TEST_COMPLETED = "test_completed"
    LOG_LINE = "log_line"

    # Generation events
    GENERATION_STARTED = "generation_started"
    GENERATION_COMPLETED = "generation_completed"
    ENDPOINT_ANALYSIS_STARTED = "endpoint_analysis_started"
    ENDPOINT_ANALYSIS_COMPLETED = "endpoint_analysis_completed"
    TESTCASE_GENERATED = "testcase_generated"
    GENERATION_ERROR = "generation_error"


class ExecutionEvent(BaseModel):
    """An event emitted during test execution or generation."""
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    resource_id: str  # execution_id or generation_id
    event_type: EventType
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class EventBus:
    """In-memory pub/sub event bus.

    Each resource (execution/generation) gets its own set of subscriber queues.
    """

    def __init__(self) -> None:
        self._queues: dict[str, list[asyncio.Queue[ExecutionEvent]]] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, resource_id: str) -> asyncio.Queue[ExecutionEvent]:
        """Register a new subscriber for a resource.

        Returns an asyncio.Queue that the subscriber can iterate over.
        """
        queue: asyncio.Queue[ExecutionEvent] = asyncio.Queue()
        async with self._lock:
            if resource_id not in self._queues:
                self._queues[resource_id] = []
            self._queues[resource_id].append(queue)
        return queue

    async def unsubscribe(self, resource_id: str, queue: asyncio.Queue[ExecutionEvent]) -> None:
        """Remove a subscriber."""
        async with self._lock:
            queues = self._queues.get(resource_id, [])
            try:
                queues.remove(queue)
            except ValueError:
                pass
            if not queues:
                self._queues.pop(resource_id, None)

    async def publish(self, event: ExecutionEvent) -> None:
        """Push an event to all subscribers of the resource."""
        async with self._lock:
            queues = list(self._queues.get(event.resource_id, []))
        for q in queues:
            try:
                await q.put(event)
            except asyncio.QueueFull:
                pass  # Drop event if subscriber is too slow

    async def close_resource(self, resource_id: str) -> None:
        """Signal completion to all subscribers by putting None on each queue."""
        async with self._lock:
            queues = self._queues.pop(resource_id, [])
        for q in queues:
            await q.put(None)  # type: ignore[arg-type]

import asyncio
import logging
import math
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Callable, Optional
import uuid

logger = logging.getLogger(__name__)

BATCH_DISPATCHER = Callable[["Batch"], None]


@dataclass
class Batch:
    post_id: int
    event_type: str
    event_ids: List[str]
    batch_size: int
    wait_time: float


class BatchingLayer:
    def __init__(self, get_count_func: Callable[[int, str], int], dispatcher: BATCH_DISPATCHER):
        self.get_count = get_count_func
        self.dispatcher = dispatcher
        self._timers: Dict[str, asyncio.TimerHandle] = {}
        self._buffers: Dict[str, List[str]] = {}
        self._lock = asyncio.Lock()

    def _make_key(self, post_id: int, event_type: str) -> str:
        return f"{event_type}:{post_id}"

    def _calculate_wait(self, total_count: int) -> float:
        return max(math.log2(total_count), 2.0)

    async def trigger(self, post_id: int, event_type: str, event_id: str):
        key = self._make_key(post_id, event_type)

        async with self._lock:
            if key not in self._buffers:
                self._buffers[key] = []
            self._buffers[key].append(event_id)

            total_count = self.get_count(post_id, event_type)
            wait_time = self._calculate_wait(total_count)

            logger.debug(
                "Batching triggered: post_id=%s, event_type=%s, total_count=%s, wait=%.2fs",
                post_id,
                event_type,
                total_count,
                wait_time,
            )

            existing_timer = self._timers.get(key)
            if existing_timer is not None:
                existing_timer.cancel()
                logger.debug("Reset existing timer for %s", key)

            self._schedule_dispatch(key, post_id, event_type, wait_time)

    def _schedule_dispatch(self, key: str, post_id: int, event_type: str, wait_time: float):
        loop = asyncio.get_event_loop()

        def fire():
            asyncio.create_task(self._dispatch(key, post_id, event_type))

        self._timers[key] = loop.call_later(wait_time, fire)
        logger.debug("Scheduled dispatch for %s in %.2fs", key, wait_time)

    async def _dispatch(self, key: str, post_id: int, event_type: str):
        async with self._lock:
            event_ids = self._buffers.get(key, [])
            if not event_ids:
                logger.debug("No events to dispatch for %s", key)
                return

            batch_size = len(event_ids)
            logger.info(
                "Dispatching batch: post_id=%s, event_type=%s, batch_size=%s",
                post_id,
                event_type,
                batch_size,
            )

            batch = Batch(
                post_id=post_id,
                event_type=event_type,
                event_ids=event_ids,
                batch_size=batch_size,
                wait_time=self._calculate_wait(self.get_count(post_id, event_type)),
            )

            self._buffers[key] = []
            if key in self._timers:
                del self._timers[key]

        try:
            self.dispatcher(batch)
        except Exception as e:
            logger.error("Dispatcher error: %s", e)


class SyncBatchingLayer:
    def __init__(self, get_count_func: Callable[[int, str], int], dispatcher: BATCH_DISPATCHER):
        self.get_count = get_count_func
        self.dispatcher = dispatcher
        self._timers: Dict[str, threading.Timer] = {}
        self._buffers: Dict[str, List[str]] = {}
        self._lock = threading.Lock()

    def _make_key(self, post_id: int, event_type: str) -> str:
        return f"{event_type}:{post_id}"

    def _calculate_wait(self, total_count: int) -> float:
        return max(math.log2(total_count), 2.0)

    def trigger(self, post_id: int, event_type: str, event_id: str):
        key = self._make_key(post_id, event_type)

        with self._lock:
            if key not in self._buffers:
                self._buffers[key] = []
            self._buffers[key].append(event_id)

            total_count = self.get_count(post_id, event_type)
            wait_time = self._calculate_wait(total_count)

            logger.debug(
                "Batching triggered: post_id=%s, event_type=%s, total_count=%s, wait=%.2fs",
                post_id,
                event_type,
                total_count,
                wait_time,
            )

            existing_timer = self._timers.get(key)
            if existing_timer is not None:
                existing_timer.cancel()
                logger.debug("Reset existing timer for %s", key)

            self._schedule_dispatch(key, post_id, event_type, wait_time)

    def _schedule_dispatch(self, key: str, post_id: int, event_type: str, wait_time: float):
        timer = threading.Timer(wait_time, self._dispatch, args=(key, post_id, event_type))
        self._timers[key] = timer
        timer.start()
        logger.debug("Scheduled dispatch for %s in %.2fs", key, wait_time)

    def _dispatch(self, key: str, post_id: int, event_type: str):
        with self._lock:
            event_ids = self._buffers.get(key, [])
            if not event_ids:
                logger.debug("No events to dispatch for %s", key)
                return

            batch_size = len(event_ids)
            logger.info(
                "Dispatching batch: post_id=%s, event_type=%s, batch_size=%s",
                post_id,
                event_type,
                batch_size,
            )

            batch = Batch(
                post_id=post_id,
                event_type=event_type,
                event_ids=event_ids,
                batch_size=batch_size,
                wait_time=self._calculate_wait(self.get_count(post_id, event_type)),
            )

            self._buffers[key] = []
            if key in self._timers:
                del self._timers[key]

        try:
            self.dispatcher(batch)
        except Exception as e:
            logger.error("Dispatcher error: %s", e)

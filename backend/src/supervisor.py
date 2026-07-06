"""
Process supervisor for xray-core.

Watches the running xray-core process and reacts to an unexpected exit
immediately (instead of waiting for the next status poll): the crash
callback runs first (engage the kill switch — fail closed), then a bounded
restart with exponential backoff is attempted. Repeated crash episodes in
a short window make the supervisor give up cleanly instead of flapping.

The policy is injected as async callables so it can be unit-tested without
a real process or firewall.
"""

import asyncio
import time
from typing import Awaitable, Callable, Optional, Sequence


class XraySupervisor:
    """Supervises one xray-core run until stop() is called or it gives up."""

    def __init__(
        self,
        *,
        wait_for_exit: Callable[[], Awaitable[Optional[int]]],
        on_crash: Callable[[Optional[int]], Awaitable[None]],
        restart: Callable[[], Awaitable[bool]],
        on_recovered: Callable[[int], Awaitable[None]],
        on_gave_up: Callable[[], Awaitable[None]],
        backoff: Sequence[float] = (1.0, 2.0, 4.0),
        max_crash_episodes: int = 3,
        stable_seconds: float = 60.0,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        """
        Args:
            wait_for_exit: Awaits the current process's exit; returns its
                return code (or None if there is no process to watch).
            on_crash: Called first on every unexpected exit (fail-closed
                actions belong here). Receives the return code.
            restart: Attempts one restart; returns True on success.
            on_recovered: Called after a successful restart with the attempt
                number (1-based).
            on_gave_up: Called when restarts are exhausted or the process
                keeps crash-looping.
            backoff: Delays (seconds) before each restart attempt.
            max_crash_episodes: Consecutive unstable crashes tolerated before
                giving up without further restarts.
            stable_seconds: A run at least this long resets the episode count.
            monotonic: Clock, injectable for tests.
        """
        self._wait_for_exit = wait_for_exit
        self._on_crash = on_crash
        self._restart = restart
        self._on_recovered = on_recovered
        self._on_gave_up = on_gave_up
        self._backoff = tuple(backoff)
        self._max_crash_episodes = max_crash_episodes
        self._stable_seconds = stable_seconds
        self._monotonic = monotonic
        self._task: Optional[asyncio.Task] = None

    def start(self) -> None:
        """Begin supervising. Idempotent while a watch task is running."""
        if self.running:
            return
        self._task = asyncio.create_task(self._run())

    @property
    def running(self) -> bool:
        return self._task is not None and not self._task.done()

    async def stop(self) -> None:
        """Cancel supervision (an intentional stop is not a crash)."""
        task = self._task
        self._task = None
        if task is None or task.done():
            return
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    async def _run(self) -> None:
        episodes = 0
        run_started = self._monotonic()
        while True:
            returncode = await self._wait_for_exit()

            if self._monotonic() - run_started >= self._stable_seconds:
                episodes = 0
            episodes += 1

            await self._on_crash(returncode)

            if episodes > self._max_crash_episodes:
                await self._on_gave_up()
                return

            recovered = False
            for attempt, delay in enumerate(self._backoff, start=1):
                await asyncio.sleep(delay)
                try:
                    ok = await self._restart()
                except Exception:
                    ok = False
                if ok:
                    recovered = True
                    await self._on_recovered(attempt)
                    break

            if not recovered:
                await self._on_gave_up()
                return

            run_started = self._monotonic()

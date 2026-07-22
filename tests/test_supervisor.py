"""Tests for backend.src.supervisor (crash detection + bounded restart)."""

import asyncio

from backend.src.supervisor import XraySupervisor


class _Harness:
    """Drives a supervisor with scriptable exits and restart outcomes."""

    def __init__(self, restart_results, clock=None):
        self._exit_queue: asyncio.Queue = asyncio.Queue()
        self.restart_results = list(restart_results)
        self.events = []
        self.clock = 0.0 if clock is None else clock

        self.supervisor = XraySupervisor(
            wait_for_exit=self._wait_for_exit,
            on_crash=self._on_crash,
            restart=self._restart,
            on_recovered=self._on_recovered,
            on_gave_up=self._on_gave_up,
            backoff=(0, 0, 0),
            max_crash_episodes=3,
            stable_seconds=60.0,
            monotonic=lambda: self.clock,
        )

    async def _wait_for_exit(self):
        return await self._exit_queue.get()

    async def _on_crash(self, returncode):
        self.events.append(("crash", returncode))

    async def _restart(self):
        if not self.restart_results:
            return False
        result = self.restart_results.pop(0)
        if isinstance(result, Exception):
            raise result
        self.events.append(("restart", result))
        return result

    async def _on_recovered(self, attempt):
        self.events.append(("recovered", attempt))

    async def _on_gave_up(self):
        self.events.append(("gave_up",))

    def crash(self, code=1):
        self._exit_queue.put_nowait(code)

    async def settle(self):
        # Let the supervisor loop process queued events.
        for _ in range(50):
            await asyncio.sleep(0)


def test_crash_triggers_kill_switch_then_restart():
    async def scenario():
        h = _Harness(restart_results=[True])
        h.supervisor.start()
        h.crash(137)
        await h.settle()
        assert h.events == [("crash", 137), ("restart", True), ("recovered", 1)]
        assert h.supervisor.running  # keeps watching the restarted process
        await h.supervisor.stop()

    asyncio.run(scenario())


def test_backoff_retries_until_success():
    async def scenario():
        h = _Harness(restart_results=[False, False, True])
        h.supervisor.start()
        h.crash()
        await h.settle()
        assert ("recovered", 3) in h.events
        await h.supervisor.stop()

    asyncio.run(scenario())


def test_gives_up_after_exhausted_attempts():
    async def scenario():
        h = _Harness(restart_results=[False, False, False])
        h.supervisor.start()
        h.crash()
        await h.settle()
        assert h.events[-1] == ("gave_up",)
        assert not h.supervisor.running

    asyncio.run(scenario())


def test_restart_exception_counts_as_failure():
    async def scenario():
        h = _Harness(restart_results=[RuntimeError("boom"), True])
        h.supervisor.start()
        h.crash()
        await h.settle()
        assert ("recovered", 2) in h.events
        await h.supervisor.stop()

    asyncio.run(scenario())


def test_crash_loop_gives_up_without_endless_restarts():
    async def scenario():
        # Restarts always succeed, but the process dies again immediately
        # (clock never advances -> runs are never "stable").
        h = _Harness(restart_results=[True] * 10)
        h.supervisor.start()
        for _ in range(4):
            h.crash()
            await h.settle()
        assert ("gave_up",) in h.events
        # Only 3 crash episodes were given a restart; the 4th went straight
        # to giving up.
        assert len([e for e in h.events if e[0] == "restart"]) == 3

    asyncio.run(scenario())


def test_stable_run_resets_crash_episodes():
    async def scenario():
        h = _Harness(restart_results=[True] * 10)
        h.supervisor.start()
        for _ in range(6):
            h.clock += 120.0  # each run was "stable" long
            h.crash()
            await h.settle()
        # Never gives up: every crash starts a fresh episode count.
        assert ("gave_up",) not in h.events
        await h.supervisor.stop()

    asyncio.run(scenario())


def test_stop_cancels_without_crash_callbacks():
    async def scenario():
        h = _Harness(restart_results=[])
        h.supervisor.start()
        await h.settle()
        await h.supervisor.stop()
        assert h.events == []
        assert not h.supervisor.running
        # Idempotent.
        await h.supervisor.stop()

    asyncio.run(scenario())


def test_start_is_idempotent_while_running():
    async def scenario():
        h = _Harness(restart_results=[])
        h.supervisor.start()
        task_before = h.supervisor._task
        h.supervisor.start()
        assert h.supervisor._task is task_before
        await h.supervisor.stop()

    asyncio.run(scenario())

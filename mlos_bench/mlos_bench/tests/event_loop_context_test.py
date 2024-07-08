#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Tests for mlos_bench.event_loop_context background thread logic."""

import asyncio
import sys
import time
from asyncio import AbstractEventLoop
from threading import Thread
from types import TracebackType
from typing import Optional, Type

import pytest
from typing_extensions import Literal

from mlos_bench.event_loop_context import EventLoopContext


class EventLoopContextCaller:
    """
    Simple class to test the EventLoopContext.

    See Also: SshService
    """

    EVENT_LOOP_CONTEXT = EventLoopContext()

    def __init__(self, instance_id: int) -> None:
        self._id = instance_id
        self._in_context = False

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self._id})"

    def __enter__(self) -> None:
        assert not self._in_context
        self.EVENT_LOOP_CONTEXT.enter()
        self._in_context = True

    def __exit__(
        self,
        ex_type: Optional[Type[BaseException]],
        ex_val: Optional[BaseException],
        ex_tb: Optional[TracebackType],
    ) -> Literal[False]:
        assert self._in_context
        self.EVENT_LOOP_CONTEXT.exit()
        self._in_context = False
        return False


@pytest.mark.filterwarnings(
    "ignore:.*(coroutine 'sleep' was never awaited).*:RuntimeWarning:.*event_loop_context_test.*:0"
)
def test_event_loop_context() -> None:
    """Test event loop context background thread setup/cleanup handling."""
    # pylint: disable=protected-access,too-many-statements

    # Should start with no event loop thread.
    assert EventLoopContextCaller.EVENT_LOOP_CONTEXT._event_loop_thread is None

    # The background thread should only be created upon context entry.
    event_loop_caller_instance_1 = EventLoopContextCaller(1)
    assert event_loop_caller_instance_1
    assert not event_loop_caller_instance_1._in_context
    assert event_loop_caller_instance_1.EVENT_LOOP_CONTEXT._event_loop_thread is None

    event_loop: Optional[AbstractEventLoop] = None

    # After we enter the instance context, we should have a background thread.
    with event_loop_caller_instance_1:
        assert event_loop_caller_instance_1._in_context
        assert (  # type: ignore[unreachable]
            isinstance(EventLoopContextCaller.EVENT_LOOP_CONTEXT._event_loop_thread, Thread)
        )
        # Give the thread a chance to start.
        # Mostly important on the underpowered Windows CI machines.
        time.sleep(0.25)
        assert EventLoopContextCaller.EVENT_LOOP_CONTEXT._event_loop_thread.is_alive()
        assert EventLoopContextCaller.EVENT_LOOP_CONTEXT._event_loop_thread_refcnt == 1
        assert EventLoopContextCaller.EVENT_LOOP_CONTEXT._event_loop is not None
        assert EventLoopContextCaller.EVENT_LOOP_CONTEXT._event_loop.is_running()
        event_loop = EventLoopContextCaller.EVENT_LOOP_CONTEXT._event_loop

        event_loop_caller_instance_2 = EventLoopContextCaller(instance_id=2)
        assert event_loop_caller_instance_2
        assert not event_loop_caller_instance_2._in_context

        with event_loop_caller_instance_2:
            assert event_loop_caller_instance_2._in_context
            assert event_loop_caller_instance_1._in_context
            assert EventLoopContextCaller.EVENT_LOOP_CONTEXT._event_loop_thread_refcnt == 2
            # We should only get one thread for all instances.
            assert (
                EventLoopContextCaller.EVENT_LOOP_CONTEXT._event_loop_thread
                is event_loop_caller_instance_1.EVENT_LOOP_CONTEXT._event_loop_thread
                is event_loop_caller_instance_2.EVENT_LOOP_CONTEXT._event_loop_thread
            )
            assert (
                EventLoopContextCaller.EVENT_LOOP_CONTEXT._event_loop
                is event_loop_caller_instance_1.EVENT_LOOP_CONTEXT._event_loop
                is event_loop_caller_instance_2.EVENT_LOOP_CONTEXT._event_loop
            )

        assert not event_loop_caller_instance_2._in_context

        # The background thread should remain running since we have another context still open.
        assert EventLoopContextCaller.EVENT_LOOP_CONTEXT._event_loop_thread_refcnt == 1
        assert EventLoopContextCaller.EVENT_LOOP_CONTEXT._event_loop_thread is not None
        assert EventLoopContextCaller.EVENT_LOOP_CONTEXT._event_loop_thread.is_alive()
        assert EventLoopContextCaller.EVENT_LOOP_CONTEXT._event_loop is not None
        assert EventLoopContextCaller.EVENT_LOOP_CONTEXT._event_loop.is_running()

        start = time.time()
        future = event_loop_caller_instance_1.EVENT_LOOP_CONTEXT.run_coroutine(
            asyncio.sleep(0.1, result="foo")
        )
        assert 0.0 <= time.time() - start < 0.1
        assert future.result(timeout=0.2) == "foo"
        assert 0.1 <= time.time() - start <= 0.2

    # Once we exit the last context, the background thread should be stopped
    # and unusable for running co-routines.

    assert (  # type: ignore[unreachable] # (false positives)
        EventLoopContextCaller.EVENT_LOOP_CONTEXT._event_loop_thread is None
    )
    assert EventLoopContextCaller.EVENT_LOOP_CONTEXT._event_loop_thread_refcnt == 0
    assert EventLoopContextCaller.EVENT_LOOP_CONTEXT._event_loop is event_loop is not None
    assert not EventLoopContextCaller.EVENT_LOOP_CONTEXT._event_loop.is_running()
    # Check that the event loop has no more tasks.
    assert hasattr(EventLoopContextCaller.EVENT_LOOP_CONTEXT._event_loop, "_ready")
    # Windows ProactorEventLoopPolicy adds a dummy task.
    if sys.platform == "win32" and isinstance(
        EventLoopContextCaller.EVENT_LOOP_CONTEXT._event_loop, asyncio.ProactorEventLoop
    ):
        assert len(EventLoopContextCaller.EVENT_LOOP_CONTEXT._event_loop._ready) == 1
    else:
        assert len(EventLoopContextCaller.EVENT_LOOP_CONTEXT._event_loop._ready) == 0
    assert hasattr(EventLoopContextCaller.EVENT_LOOP_CONTEXT._event_loop, "_scheduled")
    assert len(EventLoopContextCaller.EVENT_LOOP_CONTEXT._event_loop._scheduled) == 0

    with pytest.raises(
        AssertionError
    ):  # , pytest.warns(RuntimeWarning, match=r".*coroutine 'sleep' was never awaited"):
        future = event_loop_caller_instance_1.EVENT_LOOP_CONTEXT.run_coroutine(
            asyncio.sleep(0.1, result="foo")
        )
        raise ValueError(f"Future should not have been available to wait on {future.result()}")

    # Test that when re-entering the context we have the same event loop.
    with event_loop_caller_instance_1:
        assert EventLoopContextCaller.EVENT_LOOP_CONTEXT._event_loop is not None
        assert EventLoopContextCaller.EVENT_LOOP_CONTEXT._event_loop.is_running()
        assert EventLoopContextCaller.EVENT_LOOP_CONTEXT._event_loop is event_loop

        # Test running again.
        start = time.time()
        future = event_loop_caller_instance_1.EVENT_LOOP_CONTEXT.run_coroutine(
            asyncio.sleep(0.1, result="foo")
        )
        assert 0.0 <= time.time() - start < 0.1
        assert future.result(timeout=0.2) == "foo"
        assert 0.1 <= time.time() - start <= 0.2


if __name__ == "__main__":
    # For debugging in Windows which has issues with pytest detection in vscode.
    pytest.main(["-n1", "--dist=no", "-k", "test_event_loop_context"])

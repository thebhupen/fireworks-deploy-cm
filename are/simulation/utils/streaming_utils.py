# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

from __future__ import annotations

import concurrent.futures
import logging
import multiprocessing
import multiprocessing.context
import os
import signal
import threading
import time
from contextlib import contextmanager
from typing import Callable, Iterator, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")  # Input item type
R = TypeVar("R")  # Result type


class SequentialExecutor:
    """A sequential executor that mimics ThreadPoolExecutor interface but processes tasks synchronously."""

    def __init__(self, max_workers=None, timeout_seconds=None):
        """Initialize the sequential executor.

        :param max_workers: Ignored for sequential executor (kept for interface compatibility)
        :type max_workers: int or None
        :param timeout_seconds: Optional timeout for each task execution
        :type timeout_seconds: int or None
        """
        self._shutdown = False
        self._timeout_seconds = timeout_seconds

    def submit(self, fn: Callable, *args, **kwargs) -> concurrent.futures.Future:
        """Submit a callable to be executed sequentially with optional timeout.

        :param fn: The callable to execute
        :type fn: Callable
        :param args: Positional arguments for the callable
        :param kwargs: Keyword arguments for the callable
        :returns: A Future object representing the execution
        :rtype: concurrent.futures.Future
        :raises RuntimeError: If executor has been shut down
        """
        if self._shutdown:
            raise RuntimeError("cannot schedule new futures after shutdown")

        future = concurrent.futures.Future()

        try:
            if self._timeout_seconds:
                # Set up timeout handler for sequential processing
                def timeout_handler(signum, frame):
                    raise TimeoutError(
                        f"Operation timed out after {self._timeout_seconds} seconds"
                    )

                # Set up the timeout alarm
                old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(self._timeout_seconds)

                try:
                    result = fn(*args, **kwargs)
                    # Cancel the alarm on successful completion
                    signal.alarm(0)
                    future.set_result(result)
                except TimeoutError as e:
                    # Cancel the alarm on timeout
                    signal.alarm(0)
                    future.set_exception(e)
                except Exception as e:
                    # Cancel the alarm on any other exception
                    signal.alarm(0)
                    future.set_exception(e)
                finally:
                    # Restore the previous signal handler
                    signal.signal(signal.SIGALRM, old_handler)
            else:
                # No timeout - execute normally
                result = fn(*args, **kwargs)
                future.set_result(result)
        except Exception as e:
            future.set_exception(e)

        return future

    def shutdown(self, wait=True):
        """Shutdown the executor.

        :param wait: Ignored for sequential executor (kept for interface compatibility)
        :type wait: bool
        """
        self._shutdown = True
        # For sequential executor, there's nothing to wait for
        # since all tasks are completed synchronously

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown(wait=True)


def _worker_wrapper(queue, result_queue, fn, *args, **kwargs):
    """Worker function that wraps the actual function to handle process termination."""
    try:
        # Store the PID so parent can kill us if needed
        pid = os.getpid()
        queue.put(("pid", pid))

        # Execute the actual function
        result = fn(*args, **kwargs)
        result_queue.put(("result", result))
    except Exception as e:
        result_queue.put(("error", e))


class TerminableFuture(concurrent.futures.Future):
    """A future that allows termination of the underlying process."""

    def __init__(
        self,
        process: multiprocessing.Process | multiprocessing.context.ForkProcess,
        result_queue: multiprocessing.Queue,
    ):
        super().__init__()
        self._process = process
        self._result_queue = result_queue
        self._terminated = False
        self._pid = None

    def _check_result(self):
        """Check if result is available and process completion."""
        with self._condition:
            if super().done() or self._terminated:
                return
            # Check if process has finished
            if not self._process.is_alive():
                self._process.join()  # Clean up zombie process

                # Try to get result from queue with a short timeout
                # This allows time for the process to put the result in the queue
                # after it finishes but before we check
                try:
                    msg_type, value = self._result_queue.get(timeout=0.01)
                    if msg_type == "result":
                        self.set_result(value)
                    elif msg_type == "error":
                        self.set_exception(value)
                except Exception as e:
                    # Process died without sending result or queue is empty
                    if not super().done():
                        self.set_exception(
                            RuntimeError(f"Process terminated unexpectedly: {str(e)}")
                        )

    def result(self, timeout=None):
        """Get the result of the computation.

        :param timeout: Optional timeout to wait for result
        :type timeout: float or None
        :returns: The result of the computation
        :raises: Any exception that occurred during computation
        """
        if self._terminated:
            raise concurrent.futures.CancelledError("Future was terminated")

        # Wait for process to complete with timeout
        if timeout is not None:
            self._process.join(timeout)
            if self._process.is_alive():
                raise concurrent.futures.TimeoutError()
        else:
            self._process.join()

        self._check_result()
        return super().result(timeout)

    def exception(self, timeout=None):
        """Get the exception from the future if any.

        :param timeout: Optional timeout to wait for result
        :type timeout: float or None
        :returns: The exception that occurred, or None
        """
        if self._terminated:
            return concurrent.futures.CancelledError("Future was terminated")

        self._check_result()
        return super().exception(timeout)

    def done(self):
        """Check if the future is done.

        :returns: True if the future is done, False otherwise
        :rtype: bool
        """
        self._check_result()
        return super().done() or self._terminated

    def cancelled(self):
        """Check if the future was cancelled.

        :returns: True if the future was cancelled, False otherwise
        :rtype: bool
        """
        return self._terminated or super().cancelled()

    def running(self):
        """Check if the future is currently running.

        :returns: True if the future is running, False otherwise
        :rtype: bool
        """
        self._check_result()
        return not (super().done() or self._terminated) and self._process.is_alive()

    def cancel(self):
        """Cancel the future.

        :returns: True if successfully cancelled, False otherwise
        :rtype: bool
        """
        return self.terminate()

    def terminate(self):
        """Forcefully terminate the underlying process.

        :returns: True if successfully terminated, False if already done/terminated
        :rtype: bool
        """
        with self._condition:
            if self._terminated or super().done():
                return False

            if self._process.is_alive():
                try:
                    # First try SIGTERM for graceful shutdown
                    self._process.terminate()

                    # Wait briefly for graceful shutdown
                    self._process.join(timeout=1.0)

                    # If still alive, force kill with SIGKILL
                    if self._process.is_alive():
                        self._process.kill()
                        self._process.join()

                except (ProcessLookupError, OSError):
                    # Process already dead
                    pass

            self._terminated = True
            if not super().done():
                self.set_exception(
                    concurrent.futures.CancelledError("Process was terminated")
                )

            self._condition.notify_all()
            return True


class TerminableProcessPoolExecutor:
    """A process pool executor that allows individual processes to be terminated.

    This executor spawns individual processes for each task and tracks their PIDs,
    allowing them to be forcefully terminated with SIGTERM/SIGKILL signals.
    """

    def __init__(self, max_workers=None):
        """Initialize the terminable process pool executor.

        :param max_workers: Maximum number of worker processes
        :type max_workers: int or None
        :param mp_context: Multiprocessing context to use
        :type mp_context: multiprocessing.context or None
        :param initializer: Callable to run on each worker process startup
        :type initializer: Callable or None
        :param initargs: Arguments for the initializer
        :type initargs: tuple
        """
        if max_workers is None:
            max_workers = (os.cpu_count() or 1) + 4

        self._max_workers = max_workers
        # Use fork context on Unix systems to avoid semaphore issues on macOS
        try:
            self._mp_context = multiprocessing.get_context("fork")
        except RuntimeError:
            # Fall back to default context if fork is not available (e.g., on Windows)
            self._mp_context = multiprocessing
        self._shutdown = False
        self._active_futures = set()
        self._lock = threading.Lock()

    def submit(self, fn: Callable, *args, **kwargs) -> TerminableFuture:
        """Submit a callable to be executed in a separate process.

        :param fn: The callable to execute
        :type fn: Callable
        :param args: Positional arguments for the callable
        :param kwargs: Keyword arguments for the callable
        :returns: A TerminableFuture object representing the execution
        :rtype: TerminableFuture
        :raises RuntimeError: If executor has been shut down
        """
        if self._shutdown:
            raise RuntimeError("cannot schedule new futures after shutdown")
        # Create queues for communication
        pid_queue = self._mp_context.Queue()
        result_queue = self._mp_context.Queue()

        # Create and start process
        process = self._mp_context.Process(
            target=_worker_wrapper,
            args=(pid_queue, result_queue, fn) + args,
            kwargs=kwargs,
        )
        process.start()

        # Create terminable future
        future = TerminableFuture(process, result_queue)

        # Track active futures
        with self._lock:
            self._active_futures.add(future)

        # Add cleanup callback
        def cleanup_callback(f):
            with self._lock:
                self._active_futures.discard(future)

        future.add_done_callback(cleanup_callback)

        # Try to get PID from process
        try:
            msg_type, pid = pid_queue.get(timeout=0.1)
            if msg_type == "pid":
                future._pid = pid
        except Exception as e:
            # PID not available, that's okay
            logger.debug(f"Failed to get PID from process {str(e)}", exc_info=True)

        return future

    def shutdown(self, wait=True):
        """Shutdown the executor and all worker processes.

        :param wait: Whether to wait for pending futures to complete
        :type wait: bool
        """
        self._shutdown = True

        with self._lock:
            active_futures = list(self._active_futures)

        if not wait:
            # Terminate all running futures
            for future in active_futures:
                future.terminate()
        else:
            # Wait for futures to complete naturally
            for future in active_futures:
                try:
                    future.result(timeout=None)
                except Exception as e:
                    # Ignore exceptions during shutdown
                    logger.warning(
                        f"Exception during shutdown: {str(e)}", exc_info=True
                    )

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown(wait=True)


@contextmanager
def stream_pool(
    iterator: Iterator[T],
    process_func: Callable[..., R],  # Use ... to indicate variable arguments
    max_workers: int,
    timeout_seconds: int | None = None,
    executor_type: str = "thread",
    **kwargs,
) -> Iterator[Iterator[tuple[T, R | None, Exception | None]]]:
    """Process items from an iterator using sequential, thread-based, or process-based parallel processing.

    This function is a context manager that takes an iterator and processes its items
    using different execution strategies based on the executor_type and max_workers parameters.

    :param iterator: The source iterator providing items to process
    :type iterator: Iterator[T]
    :param process_func: Function to apply to each item from the iterator (can take additional kwargs)
    :type process_func: Callable[..., R]
    :param max_workers: Maximum number of concurrent workers. If 1, processes sequentially.
    :type max_workers: int
    :param timeout_seconds: Optional timeout for each processing operation
    :type timeout_seconds: int or None
    :param executor_type: Type of executor to use. Options: "sequential", "thread", "process"
    :type executor_type: str
    :param kwargs: Additional keyword arguments to pass to process_func
    :type kwargs: dict

    :yields: An iterator that yields tuples of (original_item, result, error) as they complete
    :rtype: Iterator[tuple[T, R | None, Exception | None]]

    - If processing succeeds, error will be None
    - If processing fails, result will be None and error will contain the exception
    - If a timeout occurs, both result will be None and error will be a TimeoutError

    .. code-block:: python

        with stream_pool(iterator, process_func, max_workers, executor_type="process") as results:
            for item, result, error in results:
                # Process results as they become available
    """
    # Choose executor based on max_workers and executor_type
    if max_workers == 1 or executor_type == "sequential":
        executor = SequentialExecutor(
            max_workers=max_workers, timeout_seconds=timeout_seconds
        )
    elif executor_type == "process":
        executor = TerminableProcessPoolExecutor(max_workers=max_workers)
    elif executor_type == "thread":
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
    else:
        raise ValueError(
            f"Invalid executor_type: {executor_type}. Must be 'sequential', 'thread', or 'process'"
        )
    futures = {}  # future -> (item, start_time)

    try:
        # Function to submit a new item to the executor if available
        def submit_next():
            try:
                item = next(iterator)
                future = executor.submit(process_func, item, **kwargs)
                start_time = time.time()
                futures[future] = (item, start_time)
                return True
            except StopIteration:
                return False

        # Initially fill the executor with up to max_workers items
        for _ in range(max_workers):
            if not submit_next():
                break

        # Create and yield the iterator
        def unified_iterator():
            # Process items as long as we have futures
            while futures:
                try:
                    # Check for timed out futures first if timeout is enabled
                    if (
                        timeout_seconds and max_workers > 1
                    ):  # Only check timeouts for parallel processing
                        current_time = time.time()
                        timed_out_futures = []
                        for future, (item, start_time) in futures.items():
                            if (
                                current_time - start_time
                            ) > timeout_seconds and future.running():
                                timed_out_futures.append(future)
                        # Cancel timed out futures and resubmit
                        for future in timed_out_futures:
                            item, start_time = futures.pop(future)
                            future.cancel()

                            # Submit a new item to replace the timed out one
                            submit_next()
                            yield (
                                item,
                                None,
                                concurrent.futures.TimeoutError(
                                    f"Operation timed out after {timeout_seconds} seconds"
                                ),
                            )

                    # Fetch completed futures
                    completed_futures = []
                    for future in futures.keys():
                        if future.done():
                            completed_futures.append(future)

                    for future in completed_futures:
                        item, start_time = futures.pop(future)
                        try:
                            result = future.result()
                            # Submit a new item to replace the completed one before yielding
                            # This keeps the executor as busy as possible
                            submit_next()
                            yield item, result, None
                        except Exception as e:
                            # Submit a new item to replace the failed one before yielding
                            submit_next()
                            yield item, None, e

                    # Wait for a short time before checking for more completions
                    time.sleep(0.01)

                except KeyboardInterrupt:
                    # Handle Ctrl+C gracefully by cancelling all futures
                    for future in list(futures.keys()):
                        future.cancel()
                    raise

        # Yield the iterator
        yield unified_iterator()

    finally:
        # Ensure executor is shut down properly
        for future in futures:
            future.cancel()
        executor.shutdown(wait=True)

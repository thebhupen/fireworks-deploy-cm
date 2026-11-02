# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import concurrent.futures
import time
from typing import Iterator

import pytest

from are.simulation.utils.streaming_utils import (
    SequentialExecutor,
    TerminableProcessPoolExecutor,
    stream_pool,
)


# Module-level functions for process executor tests (to avoid pickling issues)
def square(x):
    """Square function for testing."""
    return x * x


def process_with_delay(x):
    """Processing function with variable delay for timeout testing."""
    # Items 0, 2, 4 complete quickly, items 1, 3 take longer than the timeout
    if x % 2 == 0:
        time.sleep(0.01)  # Very quick
    else:
        time.sleep(2.0)  # Much longer than the timeout
    return x * x


def long_running_task(x):
    """Long running task for termination testing."""
    time.sleep(10)  # Long running task
    return x


@pytest.mark.parametrize("executor_type", ["sequential", "thread", "process"])
def test_stream_process_basic_functionality(executor_type):
    """Test basic functionality of stream_pool with different executor types."""
    # Create a simple iterator of numbers
    numbers = iter(range(10))

    # Process the numbers using the stream processor
    results = []
    with stream_pool(
        numbers, square, max_workers=2, executor_type=executor_type
    ) as stream:
        for item, result, error in stream:
            assert error is None
            results.append((item, result))

    # Verify the results
    assert len(results) == 10

    # Sort results by item since order may vary
    results.sort(key=lambda x: x[0])

    for i, (item, result) in enumerate(results):
        assert item == i
        assert result == i * i


def test_stream_process_exception_handling():
    """Test that stream_pool properly handles exceptions."""
    # Create a simple iterator of numbers
    numbers = iter(range(10))

    # Define a processing function that raises an exception for odd numbers
    def process_with_exceptions(x):
        if x % 2 == 1:
            raise ValueError(f"Error processing {x}")
        return x * x

    # Process the numbers using the stream processor
    success_results = []
    error_results = []

    with stream_pool(
        numbers, process_with_exceptions, max_workers=2, executor_type="thread"
    ) as stream:
        for item, result, error in stream:
            if error is None:
                success_results.append((item, result))
            else:
                error_results.append((item, error))

    # Verify the results
    assert len(success_results) == 5  # Even numbers: 0, 2, 4, 6, 8
    assert len(error_results) == 5  # Odd numbers: 1, 3, 5, 7, 9

    for item, result in success_results:
        assert item % 2 == 0
        assert result == item * item

    for item, error in error_results:
        assert item % 2 == 1
        assert isinstance(error, ValueError)
        assert str(error) == f"Error processing {item}"


@pytest.mark.parametrize("executor_type", ["thread", "process"])
def test_stream_process_timeout_handling(executor_type):
    """Test that stream_pool properly handles timeouts."""
    # Create a simple iterator of numbers
    numbers = iter(range(5))

    # Process the numbers using the stream processor with a short timeout
    success_results = []
    timeout_results = []

    # Use a timeout that's longer than the fast items but shorter than the slow ones
    with stream_pool(
        numbers,
        process_with_delay,
        max_workers=3,  # Use more workers than timeouts
        timeout_seconds=1,
        executor_type=executor_type,
    ) as stream:
        for item, result, error in stream:
            if error is None:
                success_results.append((item, result))
            elif isinstance(error, concurrent.futures.TimeoutError):
                timeout_results.append(item)
            else:
                pytest.fail(f"Unexpected error: {error}")

    # Verify the results - note that exact behavior may vary based on timing
    # We expect items 0, 2, 4 to succeed and items 1, 3 to timeout
    assert len(success_results) + len(timeout_results) == 5

    # All successful items should be even numbers
    for item, result in success_results:
        assert item % 2 == 0
        assert result == item * item

    # All timeout items should be odd numbers
    for item in timeout_results:
        assert item % 2 == 1


def test_stream_process_resource_cleanup():
    """Test that stream_pool properly cleans up resources."""
    # Create a simple iterator of numbers
    numbers = iter(range(5))

    # Define a processing function that might raise an exception
    def process_func(x):
        if x == 3:
            raise RuntimeError("Deliberate error")
        return x * x

    # Use the stream processor in a way that will cause an exception
    try:
        with stream_pool(
            numbers, process_func, max_workers=2, executor_type="thread"
        ) as stream:
            for item, result, error in stream:
                if error is not None:
                    # Re-raise the error to test exception handling
                    if isinstance(error, RuntimeError):
                        raise error
    except RuntimeError:
        pass  # Expected exception

    # If we get here without hanging, the resources were properly cleaned up


def test_stream_process_empty_iterator():
    """Test that stream_pool handles empty iterators correctly."""
    # Create an empty iterator
    empty = iter([])

    # Define a simple processing function
    def square(x):
        return x * x

    # Process the empty iterator
    results = []
    with stream_pool(empty, square, max_workers=2, executor_type="thread") as stream:
        for item, result, error in stream:
            results.append((item, result))

    # Verify that no results were produced
    assert len(results) == 0


def test_stream_process_large_dataset():
    """Test that stream_pool can handle a large dataset."""
    # Create a large iterator
    large_data = iter(range(100))

    # Define a simple processing function with some delay
    def process_with_delay(x):
        time.sleep(0.01)  # Small delay to simulate work
        return x * x

    # Process the large dataset
    results = []
    with stream_pool(
        large_data, process_with_delay, max_workers=4, executor_type="thread"
    ) as stream:
        for item, result, error in stream:
            assert error is None
            results.append((item, result))

    # Verify the results
    assert len(results) == 100
    for i, (item, result) in enumerate(sorted(results, key=lambda x: x[0])):
        assert item == i
        assert result == i * i


def test_stream_process_memory_usage():
    """Test that stream_process_with_threadpool only loads items as needed."""

    # Create a generator that tracks how many items have been yielded
    def counting_generator(n: int) -> Iterator[int]:
        items_yielded = [0]  # Use a list to allow modification in the inner function

        def increment():
            items_yielded[0] += 1
            return items_yielded[0]

        for _ in range(n):
            yield increment()

    # Create a large dataset
    large_data = counting_generator(100)

    # Define a processing function with some delay
    def process_with_delay(x):
        time.sleep(0.01)  # Small delay to simulate work
        return x * x

    # Process only a few items
    max_workers = 4
    items_to_process = 10

    results = []
    with stream_pool(
        large_data, process_with_delay, max_workers=max_workers, executor_type="thread"
    ) as stream:
        for i, (item, result, error) in enumerate(stream):
            if i >= items_to_process:
                break
            results.append((item, result))

    # Verify that we only yielded max_workers + items_to_process items from the generator
    # (max_workers items to fill the pool initially, plus one new item for each result we processed)
    assert len(results) == items_to_process
    # The highest item number should be max_workers + items_to_process
    highest_item = max(item for item, _ in results)
    assert highest_item <= max_workers + items_to_process


def test_stream_process_order_preservation():
    """Test that results are yielded in the order they complete, not the input order."""
    # Create a simple iterator of numbers
    numbers = iter(range(10))

    # Define a processing function that takes longer for smaller numbers
    def process_with_variable_delay(x):
        # Make smaller numbers take much longer to process
        if x < 5:
            time.sleep(0.2)  # Longer delay for smaller numbers
        else:
            time.sleep(0.01)  # Very short delay for larger numbers
        return x

    # Process the numbers using the stream processor with ONLY ONE worker
    # This ensures sequential processing but still tests the streaming behavior
    results = []
    with stream_pool(
        numbers,
        process_with_variable_delay,
        max_workers=10,
        executor_type="thread",
    ) as stream:
        for _, result, error in stream:
            if error is None and result is not None:
                results.append(result)

    # Print the results for debugging
    print(f"Order of results: {results}")

    # First, verify all numbers are present
    assert sorted(results) == list(range(10))

    # Then check that at least some higher numbers come before lower numbers
    # With a single worker and our delay pattern, we expect all numbers 5-9
    # to come before numbers 0-4

    # Find the position of the first small number (0-4)
    first_small_pos = min(results.index(x) for x in range(5) if x in results)

    # Find the position of the last large number (5-9)
    last_large_pos = max(results.index(x) for x in range(5, 10) if x in results)

    # The last large number should come before the first small number
    assert last_large_pos < first_small_pos, (
        f"Expected all large numbers to come before small numbers, but got: {results}"
    )


def test_stream_process_with_kwargs():
    """Test that stream_process_with_threadpool can pass additional kwargs to the processing function."""
    # Create a simple iterator of numbers
    numbers = iter(range(5))

    # Define a processing function that uses additional keyword arguments
    def process_with_kwargs(x, multiplier=1, offset=0):
        return x * multiplier + offset

    # Process the numbers using the stream processor with additional kwargs
    results = []
    with stream_pool(
        numbers,
        process_with_kwargs,
        max_workers=2,
        executor_type="thread",
        multiplier=3,  # Additional kwarg
        offset=10,  # Additional kwarg
    ) as stream:
        for item, result, error in stream:
            assert error is None
            results.append((item, result))

    # Verify the results - each number should be multiplied by 3 and have 10 added
    assert len(results) == 5
    for i, (item, result) in enumerate(sorted(results, key=lambda x: x[0])):
        assert item == i
        assert result == i * 3 + 10  # Using the multiplier and offset


def test_stream_pool_invalid_executor_type():
    """Test that stream_pool raises an error for invalid executor types."""
    numbers = iter(range(5))

    def square(x):
        return x * x

    with pytest.raises(ValueError) as exc_info:
        with stream_pool(
            numbers, square, max_workers=2, executor_type="invalid"
        ) as stream:
            list(stream)

    assert "Invalid executor_type: invalid" in str(exc_info.value)


def test_sequential_executor_direct():
    """Test SequentialExecutor class directly."""
    executor = SequentialExecutor()

    def square(x):
        return x * x

    # Submit a task
    future = executor.submit(square, 5)
    result = future.result()
    assert result == 25
    assert future.done()
    assert not future.cancelled()

    executor.shutdown()


def test_sequential_executor_with_timeout():
    """Test SequentialExecutor with timeout functionality."""
    executor = SequentialExecutor(timeout_seconds=1)

    def slow_function(x):
        time.sleep(2)  # Takes longer than timeout
        return x

    # Submit a task that will timeout
    future = executor.submit(slow_function, 5)

    with pytest.raises(TimeoutError):
        future.result()

    executor.shutdown()


def test_sequential_executor_exception_handling():
    """Test SequentialExecutor handles exceptions correctly."""
    executor = SequentialExecutor()

    def failing_function(x):
        raise ValueError(f"Test error for {x}")

    future = executor.submit(failing_function, 5)

    with pytest.raises(ValueError) as exc_info:
        future.result()

    assert "Test error for 5" in str(exc_info.value)
    assert future.done()
    assert future.exception() is not None

    executor.shutdown()


def test_sequential_executor_shutdown():
    """Test SequentialExecutor shutdown functionality."""
    executor = SequentialExecutor()

    # Test normal operation
    future = executor.submit(lambda x: x, 42)
    assert future.result() == 42

    # Shutdown executor
    executor.shutdown()

    # Test that new submissions are rejected after shutdown
    with pytest.raises(RuntimeError) as exc_info:
        executor.submit(lambda x: x, 42)

    assert "cannot schedule new futures after shutdown" in str(exc_info.value)


def test_sequential_executor_context_manager():
    """Test SequentialExecutor as a context manager."""
    with SequentialExecutor() as executor:
        future = executor.submit(lambda x: x * 2, 21)
        result = future.result()
        assert result == 42

    # After exiting context, executor should be shut down
    with pytest.raises(RuntimeError):
        executor.submit(lambda x: x, 42)


def test_terminable_process_pool_executor_basic():
    """Test TerminableProcessPoolExecutor basic functionality."""
    with TerminableProcessPoolExecutor(max_workers=2) as executor:
        future = executor.submit(square, 5)
        result = future.result()
        assert result == 25
        assert future.done()


def test_terminable_process_pool_executor_termination():
    """Test TerminableProcessPoolExecutor can terminate long-running processes."""
    with TerminableProcessPoolExecutor(max_workers=1) as executor:
        future = executor.submit(long_running_task, 5)

        # Let it start, then terminate
        time.sleep(0.1)
        success = future.terminate()
        assert success

        # Future should be cancelled/terminated
        assert future.cancelled() or future.done()


def test_stream_pool_max_workers_one_forces_sequential():
    """Test that max_workers=1 forces sequential execution regardless of executor_type."""
    numbers = iter(range(3))

    def identity(x):
        return x

    # Even with thread executor_type, max_workers=1 should use sequential
    results = []
    with stream_pool(
        numbers, identity, max_workers=1, executor_type="thread"
    ) as stream:
        for item, result, error in stream:
            assert error is None
            results.append((item, result))

    assert len(results) == 3
    # Results should be in order for sequential processing
    assert results == [(0, 0), (1, 1), (2, 2)]

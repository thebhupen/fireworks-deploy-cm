# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import logging
from unittest.mock import Mock, patch

import pytest
from requests.exceptions import HTTPError

from are.simulation.core.reliability_utils import retryable


class CustomException(Exception):
    """Custom exception for testing."""

    pass


class NonRetryableException(Exception):
    """Exception that should not be retried."""

    pass


def test_retryable_success_on_first_attempt():
    """Test that function succeeds on first attempt without retries."""
    call_count = 0

    @retryable(n_attempts=3, sleep_time_s=0.1)
    def successful_function():
        nonlocal call_count
        call_count += 1
        return "success"

    result = successful_function()
    assert result == "success"
    assert call_count == 1


def test_retryable_success_after_retries():
    """Test that function succeeds after some failed attempts."""
    call_count = 0

    @retryable(n_attempts=3, sleep_time_s=0.1)
    def eventually_successful_function():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("Not ready yet")
        return "success"

    result = eventually_successful_function()
    assert result == "success"
    assert call_count == 3


def test_retryable_exhausts_attempts():
    """Test that function fails after exhausting all retry attempts."""
    call_count = 0

    @retryable(n_attempts=3, sleep_time_s=0.1)
    def always_failing_function():
        nonlocal call_count
        call_count += 1
        raise ValueError("Always fails")

    with pytest.raises(ValueError, match="Always fails"):
        always_failing_function()

    assert call_count == 3


def test_retryable_infinite_attempts():
    """Test retryable with infinite attempts (n_attempts=None)."""
    call_count = 0

    @retryable(n_attempts=None, sleep_time_s=0.1)
    def eventually_successful_function():
        nonlocal call_count
        call_count += 1
        if call_count < 5:
            raise ValueError("Not ready yet")
        return "success"

    result = eventually_successful_function()
    assert result == "success"
    assert call_count == 5


def test_retryable_specific_exceptions():
    """Test that only specific exceptions are retried."""
    call_count = 0

    @retryable(n_attempts=3, sleep_time_s=0.1, exceptions=(ValueError,))
    def function_with_different_exceptions():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise ValueError("Retryable error")
        elif call_count == 2:
            raise TypeError("Non-retryable error")
        return "success"

    with pytest.raises(TypeError, match="Non-retryable error"):
        function_with_different_exceptions()

    assert call_count == 2


def test_retryable_non_retryable_exceptions():
    """Test that non-retryable exceptions are not retried."""
    call_count = 0

    @retryable(
        n_attempts=3,
        sleep_time_s=0.1,
        exceptions=(Exception,),
        non_retryable_exceptions=(NonRetryableException,),
    )
    def function_with_non_retryable_exception():
        nonlocal call_count
        call_count += 1
        raise NonRetryableException("Should not retry")

    with pytest.raises(NonRetryableException, match="Should not retry"):
        function_with_non_retryable_exception()

    assert call_count == 1


def test_retryable_with_retry_condition():
    """Test retryable with custom retry condition."""
    call_count = 0

    def should_retry(exception):
        return "retryable" in str(exception).lower()

    @retryable(
        n_attempts=3,
        sleep_time_s=0.1,
        exceptions=(ValueError,),
        retry_condition=should_retry,
    )
    def function_with_retry_condition():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise ValueError("This is retryable")
        elif call_count == 2:
            raise ValueError("This should not be retried")
        return "success"

    with pytest.raises(ValueError, match="This should not be retried"):
        function_with_retry_condition()

    assert call_count == 2


def test_retryable_http_error_use_case():
    """Test the specific use case from HF engine with HTTP errors and status codes."""

    def _is_retryable_http_error(error: Exception) -> bool:
        """Check if an HTTP error should be retried based on status code."""
        if not isinstance(error, HTTPError):
            return False

        if hasattr(error, "response") and hasattr(error.response, "status_code"):
            status_code = error.response.status_code
            # Don't retry 4xx client errors (400-499)
            return not (400 <= status_code < 500)
        return True

    call_count = 0

    @retryable(
        n_attempts=3,
        sleep_time_s=0.1,
        exceptions=(HTTPError,),
        retry_condition=_is_retryable_http_error,
    )
    def http_request_function():
        nonlocal call_count
        call_count += 1

        if call_count == 1:
            # Simulate 500 error (should retry)
            response_mock = Mock()
            response_mock.status_code = 500
            error = HTTPError("Server error")
            error.response = response_mock
            raise error
        elif call_count == 2:
            # Simulate 400 error (should not retry)
            response_mock = Mock()
            response_mock.status_code = 400
            error = HTTPError("Bad request")
            error.response = response_mock
            raise error

        return "success"

    with pytest.raises(HTTPError, match="Bad request"):
        http_request_function()

    assert call_count == 2


def test_retryable_preserves_function_metadata():
    """Test that the decorator preserves function metadata."""

    @retryable(n_attempts=3, sleep_time_s=0.1)
    def documented_function(x: int, y: str) -> str:
        """This function has documentation."""
        return f"{x}: {y}"

    assert documented_function.__name__ == "documented_function"
    assert documented_function.__doc__ == "This function has documentation."


def test_retryable_with_args_and_kwargs():
    """Test that retryable works with functions that have args and kwargs."""
    call_count = 0

    @retryable(n_attempts=3, sleep_time_s=0.1)
    def function_with_args(a, b, c=None, d="default"):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ValueError("Retry needed")
        return f"a={a}, b={b}, c={c}, d={d}"

    result = function_with_args("arg1", "arg2", c="kwarg1", d="kwarg2")
    assert result == "a=arg1, b=arg2, c=kwarg1, d=kwarg2"
    assert call_count == 2


@patch("time.sleep")
def test_retryable_sleep_timing(mock_sleep):
    """Test that the decorator sleeps for the correct amount of time."""
    call_count = 0

    @retryable(n_attempts=3, sleep_time_s=1.5)
    def failing_function():
        nonlocal call_count
        call_count += 1
        raise ValueError("Always fails")

    with pytest.raises(ValueError):
        failing_function()

    # Should sleep twice (after first and second failures)
    assert mock_sleep.call_count == 2
    mock_sleep.assert_called_with(1.5)


def test_retryable_logging(caplog):
    """Test that the decorator logs appropriately."""
    call_count = 0

    @retryable(n_attempts=3, sleep_time_s=0.1)
    def function_with_logging():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError(f"Attempt {call_count} failed")
        return "success"

    with caplog.at_level(logging.DEBUG):
        result = function_with_logging()

    assert result == "success"

    # Check that debug logs contain attempt information
    debug_logs = [record for record in caplog.records if record.levelname == "DEBUG"]
    assert len(debug_logs) == 3  # One for each attempt

    # Check that warning logs contain failure information
    warning_logs = [
        record for record in caplog.records if record.levelname == "WARNING"
    ]
    assert len(warning_logs) == 2  # Two failures before success


def test_retryable_invalid_parameters():
    """Test that invalid parameters raise appropriate errors."""

    with pytest.raises(AssertionError, match="You must set at least one attempt"):

        @retryable(n_attempts=0, sleep_time_s=1.0)
        def invalid_attempts():
            pass

    with pytest.raises(AssertionError, match="You must have a time larger than zero"):

        @retryable(n_attempts=3, sleep_time_s=0)
        def invalid_sleep_time():
            pass

    with pytest.raises(AssertionError, match="You must have a time larger than zero"):

        @retryable(n_attempts=3, sleep_time_s=-1.0)
        def negative_sleep_time():
            pass


def test_retryable_class_method():
    """Test that retryable works with class methods."""

    class TestClass:
        def __init__(self):
            self.call_count = 0

        @retryable(n_attempts=3, sleep_time_s=0.1)
        def method_with_retries(self, value):
            self.call_count += 1
            if self.call_count < 2:
                raise ValueError("Retry needed")
            return f"processed: {value}"

    obj = TestClass()
    result = obj.method_with_retries("test")

    assert result == "processed: test"
    assert obj.call_count == 2


def test_retryable_non_http_error_with_http_condition():
    """Test that non-HTTP errors are handled correctly with HTTP retry condition."""

    def _is_retryable_http_error(error: Exception) -> bool:
        if not isinstance(error, HTTPError):
            return False

        if hasattr(error, "response") and hasattr(error.response, "status_code"):
            status_code = error.response.status_code
            return not (400 <= status_code < 500)
        return True

    call_count = 0

    @retryable(
        n_attempts=3,
        sleep_time_s=0.1,
        exceptions=(Exception,),
        retry_condition=_is_retryable_http_error,
    )
    def function_with_non_http_error():
        nonlocal call_count
        call_count += 1
        raise ValueError("Not an HTTP error")

    # Non-HTTP error should not be retried when using HTTP retry condition
    with pytest.raises(ValueError, match="Not an HTTP error"):
        function_with_non_http_error()

    assert call_count == 1

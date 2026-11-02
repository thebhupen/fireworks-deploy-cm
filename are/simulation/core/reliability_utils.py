# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import logging
import time
from functools import wraps
from pprint import pformat
from typing import Callable, ParamSpec, Type, TypeVar

logger = logging.getLogger(__name__)
Param = ParamSpec("Param")
RetType = TypeVar("RetType")

T = TypeVar("T")
V = TypeVar("V")


def retryable(
    n_attempts: int | None,
    sleep_time_s: float,
    exceptions: tuple[Type[Exception], ...] = (Exception,),
    non_retryable_exceptions: tuple[Type[Exception], ...] = tuple(),
    retry_condition: Callable[[Exception], bool] | None = None,
):
    """
    Decorator to control retries. n_attempts None means infinite retries.

    Args:
        n_attempts: Maximum number of retry attempts (None for infinite retries).
        sleep_time_s: Time in seconds to wait between attempts.
        exceptions: Tuple of exceptions to retry on.
        non_retryable_exceptions: Tuple of exceptions to skip retries for.
        retry_condition: Optional function that takes an exception and returns True if it should be retried.
                        If provided, this function is called for exceptions in the 'exceptions' tuple
                        to determine if they should actually be retried.
    """
    assert n_attempts is None or n_attempts > 0, (
        "You must set at least one attempt, or infinite"
    )
    assert sleep_time_s > 0, "You must have a time larger than zero between attempts"

    def _decorator(fn: Callable[Param, V]) -> Callable[Param, V]:
        @wraps(fn)
        def _wrapper(*args: Param.args, **kwargs: Param.kwargs) -> V:
            attempt_idx: int = 0
            args_str = pformat(args)
            kwargs_str = pformat(kwargs)
            while True:
                try:
                    logger.debug(
                        f"Attempt {attempt_idx}/{n_attempts} Calling function '{fn.__name__}', "
                        f"with args {args_str[:1000]} ..., {kwargs_str[:1000]} ..."
                    )
                    return fn(*args, **kwargs)
                except non_retryable_exceptions as e:
                    logger.error(
                        f"Non-retryable exception encountered: {e}. Aborting retries.",
                        exc_info=True,
                    )
                    raise e
                except exceptions as e:
                    # Check if retry_condition is provided and if the exception should be retried
                    if retry_condition is not None and not retry_condition(e):
                        logger.error(
                            f"Retry condition failed for exception: {e}. Aborting retries.",
                            exc_info=True,
                        )
                        raise e

                    logger.warning(
                        f"Attempt {attempt_idx}/{n_attempts} failed! - with Exception: {e} "
                        f"Called function '{fn.__name__}' - for attempt {attempt_idx}/{n_attempts} "
                        f"with args {pformat(args_str)[:1000]} ..., {pformat(kwargs_str)[:1000]} ...",
                        exc_info=True,
                    )
                    attempt_idx += 1
                    if n_attempts is not None and attempt_idx >= n_attempts:
                        raise e
                    time.sleep(sleep_time_s)

        return _wrapper

    return _decorator

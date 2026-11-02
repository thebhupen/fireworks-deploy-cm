# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import logging
from functools import wraps
from typing import Any, Callable

logger: logging.Logger = logging.getLogger(__name__)


def injected_traceable(
    tags: list[str] | None = None,
    trace_type: str | None = None,
    meta_data: dict[str, Any] | None = None,
    log_input_args: bool = True,
) -> Callable:
    """
    Decorator for tracing methods of a class. It dynamically fetches a `tracer` method
    from the class instance and calls it to get a tracing decorator then applied to the method.
    :param tags: Tags to associate with the trace.
    :param trace_type: Type of trace to perform.
    :param meta_data: Additional metadata for the trace.
    :param log_input_args: Whether to log input arguments of the method.
    :return: A decorator to trace the method.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Check if the instance has a traceable attribute and it's callable
            tracer = getattr(self, "tracer", None)
            if tracer is None:
                # If no traceable function, call the original function
                logger.debug(f"No tracer found for {self.__class__.__name__}")
                return func(self, *args, **kwargs)
            # Fetch the traceable decorator
            trace_decorator = tracer(
                tags=tags,
                trace_type=trace_type,
                meta_data=meta_data,
                log_input_args=log_input_args,
            )
            # Apply the decorator and call the decorated function
            decorated_func = trace_decorator(func)
            return decorated_func(self, *args, **kwargs)

        return wrapper

    return decorator

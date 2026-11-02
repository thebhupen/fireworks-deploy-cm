# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import inspect
import logging
import traceback
import uuid
from functools import wraps
from typing import Any, Callable

from are.simulation.time_manager import TimeManager
from are.simulation.types import (
    Action,
    CompletedEvent,
    EventMetadata,
    EventType,
    OperationType,
)

logger = logging.getLogger(__name__)


def register_event(
    time_manager: TimeManager,
    operation_type: OperationType = OperationType.READ,
    event_type: EventType = EventType.AGENT,
    add_to_event_log: Callable | None = None,
):
    """
    This decorator is used to wrap API calls, so that we can register the event and add the appropriate CompletedEvent instance.
    The CompletedEvent instance is only added to the Event Log if the App is already registered in the environment.

    This decorator is also used to capture fictitious CompletedEvent instances when capture mode is active.
    Capture mode allows to easily simulate and create CompletedEvent instances without actually executing the API call.
    This is useful for debugging and testing, as well as defining validation trajectories.
    """

    def with_event(func: Callable) -> Callable:
        @wraps(func)  # Keeps the function signature and metadata intact
        def wrapper(*args, **kwargs) -> Any:
            self = args[0]  # Ensure self is correctly referenced
            action_id = f"{self.name}.{func.__name__}-{uuid.uuid4()}"

            # Prepare arguments for logging purposes
            try:
                # Remove self from args for Action
                bound_arguments = inspect.signature(func).bind(*args[1:], **kwargs)
                bound_arguments.apply_defaults()
                func_args = bound_arguments.arguments
                func_args.pop("self", None)  # Remove self from args for Action
                action = Action(
                    app=self,
                    function=func,
                    args=func_args,
                    operation_type=operation_type,
                )
            except Exception:
                logger.exception("Creating Action failed")
                action = Action(
                    app=self,
                    function=func,
                    args=kwargs,
                    operation_type=operation_type,
                )

            # Initialize event metadata
            event_metadata = EventMetadata(completed=False)
            event_time = time_manager.time()

            # Create and add the CompletedEvent BEFORE function execution
            event = CompletedEvent(
                event_id=f"{event_type.value}-{action_id}",
                event_type=event_type,
                action=action,
                metadata=event_metadata,
                event_time=event_time,
            )
            if add_to_event_log is not None:
                add_to_event_log(event)

            # Execute the function and capture results or exceptions
            try:
                # Remove self from args as it is already referenced in the function
                result = func(*args[1:], **kwargs)  # Directly call the function
                event_metadata.return_value = result
            except Exception as e:
                event_metadata.exception = str(e)
                event_metadata.exception_stack_trace = traceback.format_exc()
                raise e
            finally:
                event_metadata.completed = True

            return result

        return wrapper

    return with_event

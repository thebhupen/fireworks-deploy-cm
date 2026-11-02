# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import logging
import sys
import threading

from tqdm import tqdm

# Thread-local storage for scenario IDs
_thread_local = threading.local()


def set_logger_scenario_id(scenario_id: str, run_number: int | None = None) -> None:
    """
    Set the scenario ID and optional run number for the current logger context.

    Args:
        scenario_id: The scenario ID to associate with the current logger
        run_number: The run number to associate with the current logger (optional)
    """
    _thread_local.scenario_id = scenario_id
    _thread_local.run_number = run_number


def get_logger_scenario_id() -> str | None:
    """
    Get the scenario ID for the current logger context.

    Returns:
        The scenario ID associated with the current logger, or None if not set
    """
    return getattr(_thread_local, "scenario_id", None)


def get_logger_run_number() -> int | None:
    """
    Get the run number for the current logger context.

    Returns:
        The run number associated with the current logger, or None if not set
    """
    return getattr(_thread_local, "run_number", None)


class TqdmLoggingHandler(logging.Handler):
    """
    A custom logging handler that writes log messages using tqdm.write().
    This ensures that log messages don't interfere with tqdm progress bars.
    """

    def emit(self, record):
        try:
            msg = self.format(record)
            # Use tqdm.write with a file parameter to ensure consistent output
            # This helps avoid conflicts in multiprocess environments
            tqdm.write(msg, file=sys.stdout)
            self.flush()
        except (BrokenPipeError, OSError):
            # Handle broken pipe errors that can occur in multiprocess environments
            # when the main process terminates while workers are still writing
            pass
        except Exception:
            self.handleError(record)


class ScenarioAwareFormatter(logging.Formatter):
    """
    A custom formatter that includes the scenario ID in log messages if available
    and supports colored output based on log level.
    """

    # Color codes
    grey = "\x1b[38;20m"
    bold_yellow = "\x1b[33;1m"
    red = "\x1b[31;20m"
    green = "\x1b[32;20m"
    bold_red = "\x1b[31;1m"
    bold_white = "\x1b[37;1m"
    reset = "\x1b[0m"

    # Base format
    base_format = (
        "%(asctime)s - %(threadName)s - %(levelname)s - %(name)s - %(message)s"
    )

    # Color formats for different log levels
    FORMATS = {
        logging.DEBUG: grey + base_format + reset,
        logging.INFO: base_format,
        logging.WARNING: bold_yellow + base_format + reset,
        31: reset + base_format + reset,  # Custom level
        32: green + base_format + reset,  # Custom level
        33: bold_white + base_format + reset,  # Custom level
        logging.ERROR: red + base_format + reset,
        logging.CRITICAL: bold_red + base_format + reset,
    }

    def format(self, record):
        # Get the scenario ID and run number for the current thread
        scenario_id = get_logger_scenario_id()
        run_number = get_logger_run_number()

        # Add scenario ID and run number to the record if available
        if scenario_id and not hasattr(record, "scenario_id"):
            record.scenario_id = scenario_id

            # Build the prefix with scenario ID and run number if available
            if run_number is not None:
                prefix = f"[Scenario = {scenario_id}, Run = {run_number}]"
            else:
                prefix = f"[Scenario = {scenario_id}]"

            # Only add the prefix if the message doesn't already have it
            # Convert message to string first to handle non-string types (e.g., exceptions)
            msg_str = str(record.msg)
            if not msg_str.startswith(prefix):
                record.msg = f"{prefix} {msg_str}"

        # Apply color formatting based on log level
        log_fmt = self.FORMATS.get(record.levelno, self.base_format)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def configure_logging(level: int = logging.INFO, use_tqdm: bool = False) -> None:
    """
    Configure logging for the Meta Agents Research Environments application.

    This function sets up logging with appropriate handlers and formatters.
    When use_tqdm is True, it configures logging to work with tqdm progress bars
    by using TqdmLoggingHandler instead of standard StreamHandler.

    Args:
        level: The logging level (default: logging.INFO)
        use_tqdm: Whether to configure logging to work with tqdm progress bars (default: False)
    """
    # Create formatter with scenario ID awareness and color support
    standard_formatter = ScenarioAwareFormatter()

    # Create appropriate console handler based on use_tqdm flag
    if use_tqdm:
        console_handler = TqdmLoggingHandler()
    else:
        console_handler = logging.StreamHandler(stream=sys.stdout)

    console_handler.setLevel(level)
    console_handler.setFormatter(standard_formatter)

    # Configure root logger
    root_logger = logging.getLogger()  # Root logger
    root_logger.setLevel(level)
    # Clear any existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    root_logger.addHandler(console_handler)
    root_logger.propagate = True

    # Configure Meta Agents Research Environments logger
    are_simulation_logger = logging.getLogger("simulation")
    are_simulation_logger.setLevel(level)
    # Clear any existing handlers to avoid duplicates
    for handler in are_simulation_logger.handlers[:]:
        are_simulation_logger.removeHandler(handler)
    are_simulation_logger.addHandler(console_handler)
    are_simulation_logger.propagate = False

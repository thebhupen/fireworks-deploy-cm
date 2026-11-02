# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import logging


class CustomFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    bold_yellow = "\x1b[33;1m"
    red = "\x1b[31;20m"
    green = "\x1b[32;20m"
    bold_red = "\x1b[31;1m"
    bold_white = "\x1b[37;1m"
    reset = "\x1b[0m"
    format = "%(message)s"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: format,
        logging.WARNING: bold_yellow + format + reset,
        31: reset + format + reset,
        32: green + format + reset,
        33: bold_white + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def get_default_logger(logger_name: str):
    """Get the default logger with custom formatting."""
    logger = logging.getLogger(logger_name)
    logger.propagate = False
    # Remove any existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    ch = logging.StreamHandler()
    ch.setFormatter(CustomFormatter())
    logger.addHandler(ch)
    logger.setLevel(logging.DEBUG)
    return logger


def get_parent_logger(logger_name: str):
    """Get a logger that respects parent configuration."""
    # Use the parent logger name to ensure it inherits the correct log level
    logger = logging.getLogger(logger_name)
    logger.propagate = True
    # Don't remove existing handlers or add new ones
    # This allows the logger to use handlers set up by configure_logging
    return logger

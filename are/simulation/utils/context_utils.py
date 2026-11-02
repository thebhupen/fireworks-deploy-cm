# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import contextlib
import signal


def conditional_context_manager(cond, context_manager):
    """
    Return the provided context manager if condition is True, otherwise return a null context.

    This utility allows for conditional application of context managers without
    complex if-else blocks in the calling code.

    :param cond: Boolean condition determining whether to use the context manager
    :param context_manager: The context manager to conditionally apply
    :return: The provided context manager if cond is True, otherwise a nullcontext
    """
    return context_manager if cond else contextlib.nullcontext()


@contextlib.contextmanager
def time_limit(seconds):
    """
    Context manager that raises a TimeoutError if the code inside takes longer than specified seconds.

    This uses the SIGALRM signal to implement a timeout mechanism.

    :param seconds: Maximum number of seconds to allow the code to run
    :type seconds: int
    :raises TimeoutError: If the code execution exceeds the specified time limit
    :yield: Control to the code block being timed
    """

    def signal_handler(signum, frame):
        raise TimeoutError

    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)

# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


from functools import wraps

from starlette.concurrency import run_in_threadpool


def make_async(f):
    """
    By default, FastAPI runs GraphQL endpoints synchronously.
    This decorator makes a function run in a threadpool to allow concurrency.
    """

    @wraps(f)
    async def wrapper(*args, **kwargs):
        return await run_in_threadpool(f, *args, **kwargs)

    return wrapper

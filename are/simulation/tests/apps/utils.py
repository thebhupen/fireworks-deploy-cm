# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import datetime


def get_timestamp(date_str: str) -> float:
    return (
        datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        .replace(tzinfo=datetime.timezone.utc)
        .timestamp()
    )

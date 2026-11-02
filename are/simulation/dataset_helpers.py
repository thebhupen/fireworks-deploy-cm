# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import logging
import os
from functools import cache
from pathlib import Path

from are.simulation.config import ARE_SIMULATION_ROOT

logger: logging.Logger = logging.getLogger(__name__)

DEFAULT_DATA_PATH: Path = ARE_SIMULATION_ROOT / "simulation" / "datasets"


@cache
def get_data_path(default_in_repo: bool = False) -> str:
    """
    Get the path to where the datasets are physically located.

    Args:
        default_in_repo: If True, use the default in-repo data path. If
            False, use a remotely mounted path.
    """
    if env_data_path := os.environ.get("DATA_PATH"):
        return env_data_path
    if default_in_repo:
        return str(DEFAULT_DATA_PATH)
    return str(DEFAULT_DATA_PATH)

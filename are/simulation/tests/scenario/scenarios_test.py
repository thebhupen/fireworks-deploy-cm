# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import os
import re
from typing import Type

import pytest

from are.simulation.config import ARE_SIMULATION_ROOT
from are.simulation.environment import Environment, EnvironmentConfig
from are.simulation.scenarios import Scenario
from are.simulation.tests.utils import is_on_ci
from are.simulation.utils import time_limit

MAX_DURATION = 60


def test_all_scenarios_not_empty():
    from are.simulation.scenarios.utils.constants import ALL_SCENARIOS

    assert len(ALL_SCENARIOS) > 0, "No scenarios available."


def all_scenarios():
    from are.simulation.scenarios.utils.constants import ALL_SCENARIOS

    return ALL_SCENARIOS.values()


# parallelization and tests are fixed.
@pytest.mark.skipif(is_on_ci(), reason="doesn't work on CI yet")
@pytest.mark.parametrize(
    "scenario_t",
    all_scenarios(),
)
def test_run_scenario(scenario_t: Type[Scenario]):
    with time_limit(MAX_DURATION):
        scenario = scenario_t()
        scenario.duration = MAX_DURATION
        print(f"\n\nscenario: {scenario.scenario_id}")
        print(scenario)

        scenario.initialize()
        env = Environment(EnvironmentConfig(oracle_mode=True, queue_based_loop=True))
        env.exit_when_no_events = True
        env.run(scenario)
        scenario.validate(env)


def check_function_calls(scenario_file_path):
    if not os.path.exists(scenario_file_path):
        return True

    with open(scenario_file_path, "r") as file:
        content = file.read()

    pattern = r"\brun_and_validate\b\s*\("
    matches = re.findall(pattern, content)

    return len(matches) > 0


def scenarios_to_test():
    return (
        f
        for f in (ARE_SIMULATION_ROOT / "simulation" / "scenarios").iterdir()
        if f.is_dir()
        and f.name
        not in [
            "utils",
            "__pycache__",
            "universe_augmentations",
            "scenario_augmented_gaia_in_are_simulation",
            "scenario_augmented_gaia_in_are_simulation",
            "scenario_ahmad_demo",
            "scenario_yann_demo",
            "scenario_personal_assistant",
            "scenario_mcp_demo",
        ]
    )


@pytest.mark.parametrize("folder", scenarios_to_test())
def test_scenario_folders(folder):
    """Tests that all folder names in the scenarios folder start with 'scenario_' (except for 'utils' and '__pycache__'),
    and that each scenario folder containsa scenario.py and a README.md file."""

    error_messages = []

    folder_name = folder.name

    if not folder_name.startswith("scenario_"):
        error_messages.append(f"Folder does not start with 'scenario_': {folder}")

    contents = {f.name for f in folder.iterdir()}

    if "README.md" not in contents:
        error_messages.append(
            f"Folder is missing a README.md file: {folder}: {contents}"
        )

    if (
        "scenario.py" not in contents
        and "lvl1" not in folder_name
        and "template" not in folder_name
        and "prospective_memory" not in folder_name
        and "long_horizon" not in folder_name
    ):
        error_messages.append(f"Folder is missing a scenario.py file: {folder_name}")

    scenario_py_path = folder / "scenario.py"
    if not check_function_calls(str(scenario_py_path)):
        error_messages.append(
            f"Scenario in folder {folder} has no call to run_and_validate(), does it have a __main__?"
        )

    assert not error_messages, "\n".join(error_messages)


def all_scenarios_init():
    from are.simulation.scenarios.utils.constants import ALL_SCENARIOS

    return (
        scenario_func
        for scenario_name, scenario_func in ALL_SCENARIOS.items()
        if not scenario_name.startswith(
            "scenario_universe_"
        )  # Git LFS is not available on GitHub or additional info needed for initialization
        and not scenario_name.startswith("scenario_gaia_in_are_simulation")
    )


# parallelization and tests are fixed.
@pytest.mark.skipif(is_on_ci(), reason="doesn't work on CI yet")
@pytest.mark.parametrize(
    "scenario_func",
    all_scenarios_init(),
)
def test_all_scenarios_init(scenario_func):
    # redundant with test_run_scenario, but because we don't run it on github, it's good to at least do this
    scenario_func()

# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


from are.simulation.environment import Environment, EnvironmentConfig
from are.simulation.scenarios.scenario import Scenario
from are.simulation.types import EnvironmentType


def run_and_validate(scenario: Scenario, queue_based_loop: bool = True):
    try:
        scenario.initialize()

        env_config = EnvironmentConfig(
            oracle_mode=True,
            queue_based_loop=queue_based_loop,
            wait_for_user_input_timeout=None,
        )

        env = Environment(environment_type=EnvironmentType.CLI, config=env_config)
        env.run(scenario)

        validation_result = scenario.validate(env)
        print(validation_result)
    except Exception as e:
        print(f"An error occurred: {e}")

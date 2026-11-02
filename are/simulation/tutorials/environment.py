# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import time

from are.simulation.environment import Environment, EnvironmentConfig


def environment_example():
    main()


def main():
    config = EnvironmentConfig(
        # Defines the start time of the environment, it's an absolute time that is specified in terms of UNIX timestamp
        # In cases where absolute time is important (e.g. when we want to simulate a specific time of day), this needs to be specified carefully
        # By default it is set to the timestamp at the creation of the environment
        # start_time = datetime.datetime.now().timestamp() YOU CAN USE DATETIME TO SPECIFY THE START TIME
        start_time=0,
        # Defines the duration of the simulation in seconds
        # If not specified, the simulation will run until the main thread exits
        duration=10,
        # Defines the time increment in seconds, this is the time between each tick of the environment
        time_increment_in_seconds=1,
    )

    # Create environment
    env = Environment(config=config)

    # Start event loop, eent loop starts in a nother thread not the main thread, so this is non blocking
    env.start()
    print("Environment started")

    # You can do other stuff while event loop is running e.g. do nothing for a few seconds
    time.sleep(2)

    # You can also pause the simulation here for 3 seconds
    env.pause()
    print(
        f"Environment paused, time passed in the environment: {env.time_manager.time_passed():.2f} seconds"
    )
    time.sleep(3)

    # And then resume it
    env.resume()
    print(
        f"Environment resumed, time passed in the environment: {env.time_manager.time_passed():.2f} seconds"
    )

    # We create an additional time.sleep here because otherwise the simulation will end main thread exits
    time.sleep(10)


if __name__ == "__main__":
    main()

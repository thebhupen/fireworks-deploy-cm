# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import math
import random
import time

import pytest

from are.simulation.environment import Environment
from are.simulation.time_manager import TimeManager
from are.simulation.types import Event


def test_can_set_correct_time():
    """
    Test that the time manager can set the correct time
    """
    time_manager = TimeManager()
    time_manager.reset()
    created_at = time_manager.time()

    def action(env: Environment):
        return 1

    event = Event.from_function(action).at_absolute_time(time_manager.time())
    assert created_at == pytest.approx(event.event_time, abs=3)


def test_can_reset_start_time():
    """
    Test that the time manager can reset the start time
    """
    START_TIME = random.randint(0, 10000)
    time_manager = TimeManager()
    time_manager.reset(start_time=START_TIME)

    def action(env: Environment):
        return 1

    event = Event.from_function(action).at_absolute_time(time_manager.time())
    assert START_TIME == pytest.approx(event.event_time, abs=1)


def test_pause_resume():
    """
    Test that the time manager can pause and resume
    """
    #                       +-------------------------------------------+
    #  Real time            |  t = 10  |  t = 15  |  t = 18  |  t = 20  |
    #  Action               |  Start   |  Pause   |  Resume  |  Pause   |
    #                       +-------------------------------------------+
    #  time()               |  t = 10  |  t = 15  |  t = 15  |  t = 17  |
    #  time_passed()        |  t = 0   |  t = 5   |  t = 5   |  t = 7   |
    #  real_time_passed()   |  t = 0   |  t = 5   |  t = 8   |  t = 10  |
    #                       +-------------------------------------------+
    #  Offset               |  0       |  0       |  -3      |  -3      |
    #                       +-------------------------------------------+
    time_manager = TimeManager()
    time_manager.reset(start_time=10)

    assert math.floor(time_manager.time()) == 10
    assert math.floor(time_manager.time_passed()) == 0
    assert math.floor(time_manager.real_time_passed()) == 0

    # Starting timer for 5 seconds
    time.sleep(5)

    assert math.floor(time_manager.time()) == 15
    assert math.floor(time_manager.time_passed()) == 5
    assert math.floor(time_manager.real_time_passed()) == 5

    # Pausing timer for 3 seconds
    time_manager.pause()
    time.sleep(3)

    assert math.floor(time_manager.time()) == 15
    assert math.floor(time_manager.time_passed()) == 5
    assert math.floor(time_manager.real_time_passed()) == 8

    # Resuming timer for 2 seconds
    time_manager.resume()
    time.sleep(2)

    assert math.floor(time_manager.time()) == 17
    assert math.floor(time_manager.time_passed()) == 7
    assert math.floor(time_manager.real_time_passed()) == 10

    # Pausing timer again
    time_manager.pause()

    assert math.floor(time_manager.time()) == 17
    assert math.floor(time_manager.time_passed()) == 7
    assert math.floor(time_manager.real_time_passed()) == 10

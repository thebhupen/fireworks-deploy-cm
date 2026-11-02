# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


from are.simulation.tutorials.environment import environment_example
from are.simulation.tutorials.event_dag import example as event_dag_example
from are.simulation.tutorials.events import events_example
from are.simulation.tutorials.events_advanced import example as events_advanced_example


def test_events_example():
    events_example()


def test_environment_example():
    environment_example()


def test_event_dag_example():
    event_dag_example()


def test_event_advanced_example():
    events_advanced_example()

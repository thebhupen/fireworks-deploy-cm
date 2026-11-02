# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import pytest

from are.simulation.apps.agent_user_interface import AgentUserInterface, Sender
from are.simulation.environment import Environment


@pytest.fixture(autouse=True)
def disable_capture_for_test(request, capsys):
    if "needs_output" in request.keywords:
        capsys.disabled()


def test_send_message_to_user():
    app = AgentUserInterface()
    environment = Environment()
    environment.register_apps([app])
    content = "Hello, User!"
    app.send_message_to_user(content)
    assert len(app.messages) == 1
    assert app.messages[0].content == content
    assert app.messages[0].sender == Sender.AGENT


def test_get_last_message_from():
    app = AgentUserInterface()
    environment = Environment()
    environment.register_apps([app])
    app.send_message_to_user("First message")
    app.send_message_to_user("Second message")
    response = app.get_last_message_from_agent()
    assert "Second message" in response.content


def test_send_message_to_agent():
    app = AgentUserInterface()
    environment = Environment()
    environment.register_apps([app])
    content = "Hello, Agent!"
    app.send_message_to_agent(content)
    assert len(app.messages) == 1
    assert app.messages[0].content == content
    assert app.messages[0].sender == Sender.USER


def test_get_all_messages():
    app = AgentUserInterface()
    environment = Environment()
    environment.register_apps([app])
    app.send_message_to_user("Hello, User!")
    app.send_message_to_agent("Hello, Agent!")
    messages = app.get_all_messages()
    assert any("Hello, Agent!" in m.content for m in messages)
    assert any("Hello, User!" in m.content for m in messages)

# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


from unittest.mock import MagicMock

from are.simulation.agents.user_proxy import UserProxyLLM


def test_user_proxy_llm_reply():
    mock_llm = MagicMock()
    mock_llm.return_value = "Mocked response", None
    user_proxy = UserProxyLLM(llm=mock_llm)

    response = user_proxy.reply("Hello")
    assert response == "Mocked response"
    assert user_proxy.history[-1] == {"role": "assistant", "content": "Mocked response"}


def test_user_proxy_llm_init_conversation():
    mock_llm = MagicMock()
    mock_llm.return_value = "Hello", None
    user_proxy = UserProxyLLM(llm=mock_llm)

    response = user_proxy.init_conversation()
    assert response == "Hello"
    assert user_proxy.history[-1] == {
        "role": "assistant",
        "content": "Hello",
    }

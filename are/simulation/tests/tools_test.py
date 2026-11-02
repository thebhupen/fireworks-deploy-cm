# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


from are.simulation.tools import SystemPrompt


def test_system_prompt():
    stp = SystemPrompt(
        prompt="You are a helpful assistant.\n",
        zero_shot_examples=["Example 1", "Example 2"],
        conclusion="\nNow you can start helping me.",
    )
    assert (
        str(stp)
        == "You are a helpful assistant.\nExample 1\n\n---\nExample 2\nNow you can start helping me."
    )
    assert (
        stp.generate_with_augmentation(0)
        == "You are a helpful assistant.\n\nNow you can start helping me."
    )
    assert str(stp) == stp.generate_with_augmentation(1)

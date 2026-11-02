# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import inspect
import random
from dataclasses import dataclass, field
from functools import wraps
from typing import Union


@dataclass(frozen=True)
class SystemPrompt:
    prompt: str
    zero_shot_examples: list[str] = field(default_factory=list)
    conclusion: str = ""

    def __str__(self):
        """Transforms the SystemPrompt into a string that can be used as a prompt for the LLM.

        Example:
        ````
        stp = SystemPrompt(
            prompt="You are a helpful assistant.\n",
            zero_shot_examples=["Example 1", "Example 2"],
            conclusion="\nNow you can start helping me."
        )
        str(stp) # "You are a helpful assistant.Example 1\n\n---\nExample 2\nNow you can start helping me."
        stp.generate_with_augmentation(0) # "You are a helpful assistant.\n\nNow you can start helping me."

        ````
        Returns: str
        """
        return self.generate_with_augmentation(
            probability_to_keep_examples=1, shuffle_examples=False
        )

    def generate_with_augmentation(
        self, probability_to_keep_examples: float = 1, shuffle_examples: bool = False
    ) -> str:
        examples = []
        for example in self.zero_shot_examples:
            if random.random() < probability_to_keep_examples:
                examples.append(example)
        if len(examples) > 0 and shuffle_examples:
            random.shuffle(examples)
        return self.prompt + "\n\n---\n".join(examples) + self.conclusion


def validate_after_init(cls, do_validate_forward: bool = True):
    original_init = cls.__init__

    @wraps(original_init)
    def new_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self.validate_arguments(do_validate_forward=do_validate_forward)

    cls.__init__ = new_init
    return cls


def handle_agent_inputs(*args, **kwargs):
    # No type conversion needed if only using strings
    return args, kwargs


def handle_agent_outputs(output, output_type=None):
    # Just return the output directly since we're only using strings
    return output


class Tool:
    """
    A class for the functions used by the agent. Subclass this and implement the `forward` method as well as the
    required class attributes.
    """

    name: str
    description: str
    inputs: dict[str, dict[str, Union[str, type]]]
    output_type: str = "string"
    additional_hints: str = ""  # Additional hints to provide to the agents
    zero_shot_examples: list[str] = []  # list of zero shot examples that can be used

    def __init__(self, *args, **kwargs):
        self.is_initialized = False

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        validate_after_init(cls, do_validate_forward=False)

    def validate_arguments(self, do_validate_forward: bool = True):
        required_attributes = {
            "description": str,
            "name": str,
            "inputs": dict,
            "output_type": str,
        }
        authorized_types = [
            "string",
            "integer",
            "number",
            "image",
            "audio",
            "any",
            "boolean",
        ]

        for attr, expected_type in required_attributes.items():
            attr_value = getattr(self, attr, None)
            if attr_value is None:
                raise TypeError(f"You must set an attribute {attr}.")
            if not isinstance(attr_value, expected_type):
                raise TypeError(
                    f"Attribute {attr} should have type {expected_type.__name__}, got {type(attr_value)} instead."
                )
        for input_name, input_content in self.inputs.items():
            assert isinstance(input_content, dict), (
                f"Input '{input_name}' should be a dictionary."
            )
            assert "type" in input_content and "description" in input_content, (
                f"Input '{input_name}' should have keys 'type' and 'description', has only {list(input_content.keys())}."
            )
            if input_content["type"] not in authorized_types:
                raise Exception(
                    f"Input '{input_name}': type '{input_content['type']}' is not an authorized value, should be one of {authorized_types}."
                )

        assert getattr(self, "output_type", None) in authorized_types
        if do_validate_forward:
            signature = inspect.signature(self.forward)
            if not set(signature.parameters.keys()) == set(self.inputs.keys()):
                raise Exception(
                    "Tool's 'forward' method should take 'self' as its first argument, then its next arguments should match the keys of tool attribute 'inputs'."
                )

    def forward(self, *args, **kwargs):
        return NotImplementedError("Write this method in your subclass of `Tool`.")

    def __call__(self, *args, **kwargs):
        args, kwargs = handle_agent_inputs(*args, **kwargs)
        outputs = self.forward(*args, **kwargs)
        return handle_agent_outputs(outputs, self.output_type)

    def setup(self):
        """
        Overwrite this method here for any operation that is expensive and needs to be executed before you start using
        your tool. Such as loading a big model.
        """
        self.is_initialized = True

    def __repr__(self) -> str:
        repr = f"{self.name} : {self.description}"
        if self.additional_hints != "":
            repr += f"\n{self.additional_hints}"
        if len(self.zero_shot_examples) > 0:
            repr += "\n" + "\n".join(self.zero_shot_examples)
        return repr

    def __str__(self) -> str:
        return self.__repr__()

    def generate_random_variation_description(
        self, additional_hints_ratio: float, zero_shot_example_ratio: float
    ) -> str:
        """Generate a random variation of the tool description.

        Args:
            additional_hints_ratio (float): frequency at which additional hints should be included in the variation
            zero_shot_example_ratio (float): frequency at which zero shot examples should be included in the variation

        Returns:
            str: the tool description
        """
        description = self.description
        if self.additional_hints != "" and random.random() < additional_hints_ratio:
            description += "\n" + self.additional_hints

        for example in self.zero_shot_examples:
            if random.random() < zero_shot_example_ratio:
                description += "\n" + example

        return description

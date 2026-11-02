# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


"""
Shared parameter definitions for Meta Agents Research Environments CLI tools.

This module provides common Click options that can be reused across different CLI tools
to ensure consistency in parameter names, help text, and behavior.
"""

import click

from are.simulation.agents.agent_builder import AgentBuilder
from are.simulation.config import PROVIDERS
from are.simulation.utils import DEFAULT_MODEL, DEFAULT_PROVIDER


# Model Configuration Options
def model_option():
    """
    Create a Click option for specifying the model used in the agent.

    :returns: Click option decorator for model parameter
    :rtype: click.Option
    """
    return click.option(
        "-m",
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help="Model used in the agent",
    )


def provider_option():
    """
    Create a Click option for specifying the model provider.

    Standardized to --provider with -mp short option. Includes --model_provider
    alias for backward compatibility.

    :returns: Click option decorator for provider parameter
    :rtype: click.Option
    """
    return click.option(
        "-mp",
        "--provider",
        "--model_provider",  # Alias for backward compatibility
        type=click.Choice(PROVIDERS),
        required=False,
        default=DEFAULT_PROVIDER,
        help="Provider of the model",
    )


def endpoint_option():
    """
    Create a Click option for specifying the endpoint URL.

    :returns: Click option decorator for endpoint parameter
    :rtype: click.Option
    """
    return click.option(
        "--endpoint",
        type=str,
        required=False,
        help="URL of the endpoint to contact for running the agent's model",
    )


# Agent Configuration Options
def agent_option():
    """
    Create a Click option for specifying the agent to use.

    :returns: Click option decorator for agent parameter
    :rtype: click.Option
    """
    return click.option(
        "-a",
        "--agent",
        type=click.Choice(AgentBuilder().list_agents()),
        required=False,
        help="Agent to use for running the Scenario",
    )


# Logging Configuration
def log_level_option():
    """
    Create a Click option for setting the logging level.

    :returns: Click option decorator for log level parameter
    :rtype: click.Option
    """
    return click.option(
        "--log-level",
        type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
        default="INFO",
        help="Set the logging level",
    )


# Runtime Configuration Options
def oracle_option():
    """
    Create a Click option for enabling Oracle mode.

    In Oracle mode, oracle events (user defined agent events) are executed.

    :returns: Click option decorator for oracle parameter
    :rtype: click.Option
    """
    return click.option(
        "-o",
        "--oracle",
        is_flag=True,
        default=False,
        help="Run the scenario in Oracle mode where oracle events (i.e. user defined agent events) are ran",
    )


def simulated_generation_time_mode_option():
    """
    Create a Click option for specifying LLM generation time simulation mode.

    :returns: Click option decorator for simulated generation time mode parameter
    :rtype: click.Option
    """
    return click.option(
        "--simulated_generation_time_mode",
        type=click.Choice(["measured", "fixed", "random"]),
        default="measured",
        required=False,
        help="Mode for simulating LLM generation time",
    )


def noise_option():
    """
    Create a Click option for enabling noise augmentation.

    Enables noise augmentation with tool augmentation and environment events configs.

    :returns: Click option decorator for noise parameter
    :rtype: click.Option
    """
    return click.option(
        "--noise",
        is_flag=True,
        default=False,
        help="Enable noise augmentation with tool augmentation and environment events configs",
    )


def max_concurrent_scenarios_option():
    """
    Create a Click option for specifying maximum concurrent scenarios.

    :returns: Click option decorator for max concurrent scenarios parameter
    :rtype: click.Option
    """
    return click.option(
        "--max_concurrent_scenarios",
        type=int,
        default=None,
        help="Maximum number of concurrent scenarios to run. If not specified, automatically sets based on the number of CPUs",
    )


def output_dir_option():
    """
    Create a Click option for specifying output directory.

    Standardized to --output_dir with --dump_dir alias for backward compatibility.

    :returns: Click option decorator for output directory parameter
    :rtype: click.Option
    """
    return click.option(
        "--output_dir",
        "--dump_dir",  # Alias for backward compatibility
        type=str,
        default=None,
        help="Directory to dump the scenario states and logs",
    )


# JSON Parameter Parsing
def kwargs_option():
    """
    Create a Click option for additional keyword arguments as JSON.

    :returns: Click option decorator for kwargs parameter
    :rtype: click.Option
    """
    return click.option(
        "--kwargs",
        type=str,
        default="{}",
        help="Additional keyword arguments to pass to the scenario initialize function as a JSON string",
    )


def multi_kwargs_option():
    """
    Create a Click option for multiple additional scenario-based keyword arguments as JSON.

    :returns: Click option decorator for kwargs parameter
    :rtype: click.Option
    """
    return click.option(
        "--multi_kwargs",
        type=str,
        default="[{}]",
        help="A list of additional keyword arguments to pass to the scenario creation function as a JSON string. Will create multiple scenarios with the same kwargs, with the only difference being the arguments in this list.",
    )


def scenario_kwargs_option():
    """
    Create a Click option for scenario initialization arguments as JSON.

    :returns: Click option decorator for scenario kwargs parameter
    :rtype: click.Option
    """
    return click.option(
        "--scenario_kwargs",
        type=str,
        default="{}",
        help="Additional keyword arguments to pass to initialize the scenario as a JSON string",
    )


def multi_scenario_kwargs_option():
    """
    Create a Click option for multiple additional scenario initialization arguments as JSON.

    :returns: Click option decorator for kwargs parameter
    :rtype: click.Option
    """
    return click.option(
        "--multi_scenario_kwargs",
        type=str,
        default="[{}]",
        help="A list of additional keyword arguments to pass while initializing the scenario as an array of json strings. Will initialize the same scenario with different arguments.",
    )


# Composite option groups for common parameter sets
def core_agent_options():
    """
    Decorator that adds core agent configuration options.

    Adds model, provider, endpoint, and agent options to the decorated function.

    :returns: Decorator function that applies core agent options
    :rtype: callable
    """

    def decorator(func):
        func = model_option()(func)
        func = provider_option()(func)
        func = endpoint_option()(func)
        func = agent_option()(func)
        return func

    return decorator


def runtime_config_options():
    """
    Decorator that adds common runtime configuration options.

    Adds oracle, simulated generation time mode, noise, and max concurrent
    scenarios options to the decorated function.

    :returns: Decorator function that applies runtime configuration options
    :rtype: callable
    """

    def decorator(func):
        func = oracle_option()(func)
        func = simulated_generation_time_mode_option()(func)
        func = noise_option()(func)
        func = max_concurrent_scenarios_option()(func)
        return func

    return decorator


def logging_config_options():
    """
    Decorator that adds logging configuration options.

    Adds log level option to the decorated function.

    :returns: Decorator function that applies logging configuration options
    :rtype: callable
    """

    def decorator(func):
        func = log_level_option()(func)
        return func

    return decorator


def output_config_options():
    """
    Decorator that adds output configuration options.

    Adds output directory option to the decorated function.

    :returns: Decorator function that applies output configuration options
    :rtype: callable
    """

    def decorator(func):
        func = output_dir_option()(func)
        return func

    return decorator


def json_config_options():
    """
    Decorator that adds JSON parameter options.

    Adds kwargs and scenario_kwargs options to the decorated function.

    :returns: Decorator function that applies JSON configuration options
    :rtype: callable
    """

    def decorator(func):
        func = kwargs_option()(func)
        func = multi_kwargs_option()(func)
        func = multi_scenario_kwargs_option()(func)
        func = scenario_kwargs_option()(func)
        return func

    return decorator


def common_options():
    """
    Decorator that adds the most common options shared across all CLIs.

    Combines core agent options and logging configuration options.

    :returns: Decorator function that applies common options
    :rtype: callable
    """

    def decorator(func):
        func = core_agent_options()(func)
        func = logging_config_options()(func)
        return func

    return decorator

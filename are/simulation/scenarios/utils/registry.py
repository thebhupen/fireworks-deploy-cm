# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


# Use pkg_resources for entry point discovery
import importlib.metadata as importlib_metadata
import logging
from typing import Callable, Type, TypeVar

from are.simulation.scenarios import registration
from are.simulation.scenarios.scenario import Scenario

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=Scenario)

# Entry point group name for scenarios
SCENARIO_ENTRY_POINT_GROUP = "are.simulation.scenarios"


class ScenarioRegistry:
    """
    A registry for scenario classes.

    This class manages the registration, discovery, and retrieval of scenario classes.
    It uses entry points to discover scenarios from installed packages.
    """

    def __init__(self):
        """
        Initialize an empty scenario registry.
        """
        self._registry: dict[str, Type[Scenario]] = {}
        self._scenarios_discovered = False

    def register(self, scenario_id: str) -> Callable[[Type[T]], Type[T]]:
        """
        Decorator to register a scenario class with a specific ID.

        Usage:
            @registry.register('scenario_id')
            class MyScenario(Scenario):
                ...

        Args:
            scenario_id: The ID to register the scenario under

        Returns:
            A decorator function that registers the scenario class
        """

        def decorator(cls: Type[T]) -> Type[T]:
            if not issubclass(cls, Scenario):
                raise TypeError(f"Class {cls.__name__} is not a subclass of Scenario")

            # Set the scenario_id on the class
            cls.scenario_id = scenario_id

            # Register the scenario class in the registry
            if scenario_id in self._registry:
                logger.warning(
                    f"Scenario ID '{scenario_id}' is already registered. "
                    f"Overwriting previous registration."
                )

            self._registry[scenario_id] = cls
            logger.debug(
                f"Registered scenario '{scenario_id}' with class {cls.__name__}"
            )

            return cls

        return decorator

    def _discover_and_import_scenarios(self) -> None:
        """
        Discover and import all scenario modules using entry points.

        This method looks for entry points in the 'are.simulation.scenarios' group
        and loads them. Each entry point should point to a function that
        registers one or more scenarios with this registry.
        """
        if self._scenarios_discovered:
            return

        # Count how many entry points we've loaded
        loaded_entry_points = 0

        # first load all the scenarios provided in are.simulation
        registration.register_builtin_scenarios(self)

        # Discover scenarios via entry points
        for entry_point in importlib_metadata.entry_points(
            group=SCENARIO_ENTRY_POINT_GROUP
        ):
            try:
                logger.info(
                    f"Loading scenario entry point: {entry_point.name} from {entry_point.dist}"
                )

                # Load the entry point
                scenario_loader = entry_point.load()

                # If it's a callable, call it with this registry
                if callable(scenario_loader):
                    scenario_loader(self)
                    loaded_entry_points += 1
                else:
                    logger.warning(
                        f"Entry point {entry_point.name} is not callable, skipping"
                    )
            except Exception as e:
                logger.warning(
                    f"Failed to load scenario entry point {entry_point.name}: {e}",
                    exc_info=True,
                )

        self._scenarios_discovered = True
        logger.info(
            f"Discovered and loaded {loaded_entry_points} scenario entry points"
        )

    def get_scenario(self, scenario_id: str) -> Type[Scenario]:
        """
        Get a scenario class by its ID.

        Args:
            scenario_id: The ID of the scenario to retrieve

        Returns:
            The scenario class

        Raises:
            KeyError: If no scenario with the given ID is registered
        """
        # Ensure scenarios are discovered before accessing the registry
        if not self._scenarios_discovered:
            self._discover_and_import_scenarios()

        if scenario_id not in self._registry:
            raise KeyError(f"No scenario registered with ID '{scenario_id}'")

        return self._registry[scenario_id]

    def get_all_scenarios(self) -> dict[str, Type[Scenario]]:
        """
        Get all registered scenarios.

        Returns:
            A dictionary mapping scenario IDs to scenario classes
        """
        # Ensure scenarios are discovered before accessing the registry
        if not self._scenarios_discovered:
            self._discover_and_import_scenarios()

        return self._registry

    def reset(self) -> None:
        """
        Reset the registry to its initial state.
        This is primarily useful for testing.
        """
        self._registry.clear()
        self._scenarios_discovered = False


# Create a singleton instance of the registry
registry = ScenarioRegistry()


# For backward compatibility and ease of use, provide the decorator as a function
def register_scenario(scenario_id: str) -> Callable[[Type[T]], Type[T]]:
    """
    Decorator to register a scenario class with a specific ID.
    This is a convenience wrapper around registry.register.

    Usage:
        @register_scenario('scenario_id')
        class MyScenario(Scenario):
            ...

    Args:
        scenario_id: The ID to register the scenario under

    Returns:
        A decorator function that registers the scenario class
    """
    return registry.register(scenario_id)

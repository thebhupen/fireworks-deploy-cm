# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


from unittest.mock import MagicMock, patch

import pytest

from are.simulation.scenarios.scenario import Scenario
from are.simulation.scenarios.utils.registry import ScenarioRegistry, register_scenario


@pytest.fixture
def registry():
    """
    Create a fresh ScenarioRegistry instance for each test.
    This ensures tests are completely isolated from each other.
    """
    return ScenarioRegistry()


@pytest.fixture
def mock_scenario_discovery(registry):
    """
    Mock the scenario discovery process to avoid actual imports during testing.
    This makes tests faster and more isolated.
    """
    # Create a mock scenario class
    mock_scenario = MagicMock()
    mock_scenario.scenario_id = "scenario_find_image_file"

    # Add it to the registry
    registry._registry["scenario_find_image_file"] = mock_scenario

    # Mock the discovery method to do nothing
    with patch.object(registry, "_discover_and_import_scenarios") as mock_discover:

        def side_effect():
            registry._scenarios_discovered = True

        mock_discover.side_effect = side_effect
        yield mock_discover


def test_scenarios_are_registered(registry):
    """
    Test that scenarios are properly registered in the registry.
    This test verifies that the registration mechanism works.
    """

    # Create a mock scenario class that inherits from Scenario
    class MockScenario(Scenario):
        pass

    # Register it with the registry
    decorator = registry.register("test_scenario")
    scenario_class = decorator(MockScenario)

    # Verify it was registered
    assert "test_scenario" in registry._registry
    assert registry._registry["test_scenario"] is scenario_class


def test_get_all_scenarios(registry, mock_scenario_discovery):
    """
    Test that get_all_scenarios returns all registered scenarios.
    This test verifies that the lazy-loading auto-discovery mechanism is working.
    """
    # Get all scenarios from the registry - this should trigger discovery
    registered_scenarios = registry.get_all_scenarios()

    # Ensure discovery was triggered
    assert mock_scenario_discovery.called

    # Ensure we have the mock scenario registered
    assert "scenario_find_image_file" in registered_scenarios

    # Print the number of registered scenarios for information
    print(f"Found {len(registered_scenarios)} registered scenarios")


def test_get_scenario(registry, mock_scenario_discovery):
    """
    Test that get_scenario returns the correct scenario.
    """
    # Get a specific scenario - this should trigger discovery
    scenario = registry.get_scenario("scenario_find_image_file")

    # Ensure discovery was triggered
    assert mock_scenario_discovery.called

    # Ensure we got the right scenario
    assert scenario is registry._registry["scenario_find_image_file"]


def test_scenario_modules_discoverable():
    """
    Test that scenario modules can be discovered using the new registration module.
    This helps verify that the auto-discovery mechanism can find scenario files.
    """
    import os
    from pathlib import Path

    # Get the path to the scenarios directory
    scenarios_dir = Path(__file__).parent.parent.parent / "scenarios"

    # Verify the scenarios directory exists
    assert scenarios_dir.exists(), f"Scenarios directory not found at {scenarios_dir}"

    # Count the number of potential scenario modules using the same logic as in registration.py
    scenario_modules = []

    # Method 1: Find Python files that match our naming convention
    for root, _, files in os.walk(scenarios_dir):
        # Skip utility directories and hidden directories
        if (
            any(d in root for d in ["/utils/", "/tests/", "/__pycache__"])
            or "/." in root
        ):
            continue

        # Look for Python files that might contain scenarios
        for file in files:
            # Skip non-Python files and __init__.py
            if not file.endswith(".py") or file == "__init__.py":
                continue

            # Skip files that don't match our naming convention
            if "scenario" not in file.lower() and not file.endswith("_scenario.py"):
                continue

            scenario_modules.append(os.path.join(root, file))

    # Ensure we found some scenario modules
    assert len(scenario_modules) > 0, (
        "No scenario modules found. Check the directory structure."
    )

    # Print the number of potential scenario modules for information
    print(f"Found {len(scenario_modules)} potential scenario modules")

    from unittest.mock import MagicMock

    # Test that our registration module can find and import these modules
    from are.simulation.scenarios.registration import register_builtin_scenarios

    # Create a mock registry
    mock_registry = MagicMock()

    # Call the registration function
    register_builtin_scenarios(mock_registry)

    # Verify that the function completed without errors
    # (We can't easily verify which modules were imported, but we can at least
    # check that the function ran without raising exceptions)


def test_lazy_loading(registry):
    """
    Test that scenarios are only discovered when needed.
    This verifies that the lazy-loading mechanism is working.
    """
    # Verify that scenarios are not discovered initially
    assert not registry._scenarios_discovered, (
        "Scenarios should not be discovered until requested"
    )

    # Patch the discovery method to just set the flag
    with patch.object(registry, "_discover_and_import_scenarios") as mock_discover:

        def side_effect():
            registry._scenarios_discovered = True

        mock_discover.side_effect = side_effect

        # Call get_all_scenarios which should trigger discovery
        _ = registry.get_all_scenarios()

        # Verify discovery was triggered
        assert mock_discover.called

        # Verify that scenarios are now discovered
        assert registry._scenarios_discovered, (
            "Scenarios should be discovered after calling get_all_scenarios"
        )


def test_registry_reset(registry):
    """
    Test that the registry can be reset.
    This verifies that the reset method works correctly.
    """
    # Add a mock scenario to the registry
    registry._registry["test_scenario"] = MagicMock()
    registry._scenarios_discovered = True

    # Verify the registry has content
    assert len(registry._registry) > 0
    assert registry._scenarios_discovered

    # Reset the registry
    registry.reset()

    # Verify that scenarios are no longer discovered
    assert not registry._scenarios_discovered, (
        "Registry should be reset to undiscovered state"
    )

    # Verify that the registry is empty
    assert len(registry._registry) == 0, "Registry should be empty after reset"


def test_matches_past():
    """
    Test that the registry discovers all expected scenarios.
    This test ensures that our scenario discovery mechanism is working correctly
    by comparing the discovered scenarios with a known list of benchmark scenarios.
    It also verifies that the retrieved scenarios have the correct scenario_ids.
    """
    from are.simulation.scenarios.utils.import_utils import import_scenario
    from are.simulation.scenarios.utils.registry import registry

    BENCHMARK_SCENARIOS = [
        "scenario_find_image_file.scenario",
    ]

    # Get all scenarios from the registry
    all_scenarios = registry.get_all_scenarios()
    registry_ids = set(all_scenarios.keys())

    # Try to import each benchmark scenario and get its actual ID
    benchmark_ids = set()
    missing_modules = []
    scenario_id_to_class = {}

    for module_name in BENCHMARK_SCENARIOS:
        try:
            # Try to import the scenario
            scenario_class = import_scenario(module_name)
            # Add the actual scenario ID to our set
            scenario_id = scenario_class.scenario_id
            benchmark_ids.add(scenario_id)
            scenario_id_to_class[scenario_id] = scenario_class
        except Exception as e:
            # If import fails, add to missing modules list
            missing_modules.append((module_name, str(e)))
            continue

    assert len(missing_modules) == 0, f"Missing modules: {missing_modules}"
    assert len(benchmark_ids) <= len(registry_ids), (
        f"Missing scenarios {benchmark_ids - registry_ids}"
    )

    # Verify that the retrieved scenarios have the correct scenario_ids
    for scenario_id, expected_class in scenario_id_to_class.items():
        # Get the scenario from the registry
        retrieved_class = registry.get_scenario(scenario_id)

        # Verify that the retrieved class has the correct scenario_id
        assert retrieved_class.scenario_id == scenario_id, (
            f"Retrieved scenario has incorrect scenario_id: expected '{scenario_id}', got '{retrieved_class.scenario_id}'"
        )

        # Verify that the retrieved class is the same as the imported class
        assert retrieved_class is expected_class, (
            f"Retrieved scenario class for '{scenario_id}' does not match the imported class"
        )


def test_scenario_id_propagation():
    """
    Test that the scenario_id set on the class during registration
    is properly propagated to instances of the class.
    """

    # Create a test scenario class
    @register_scenario("test_scenario_id")
    class TestScenario(Scenario):
        pass

    # Create an instance of the scenario class
    scenario_instance = TestScenario()

    # Check that the class has the scenario_id
    assert TestScenario.scenario_id == "test_scenario_id"

    # Check that the instance has the scenario_id
    assert scenario_instance.scenario_id == "test_scenario_id"

    # Create another instance and verify it also has the correct scenario_id
    another_instance = TestScenario()
    assert another_instance.scenario_id == "test_scenario_id"


def test_global_registry_get_scenario():
    """
    Test that when we register scenarios with the global registry and
    retrieve them by ID, we get the correct scenario back.
    """
    from are.simulation.scenarios.utils.registry import register_scenario, registry

    # Reset the global registry to ensure a clean state
    registry.reset()

    # Create and register multiple scenario classes
    @register_scenario("scenario_one")
    class ScenarioOne(Scenario):
        description: str = "First test scenario"

    @register_scenario("scenario_two")
    class ScenarioTwo(Scenario):
        description: str = "Second test scenario"

    @register_scenario("scenario_three")
    class ScenarioThree(Scenario):
        description: str = "Third test scenario"

    # Retrieve scenarios by ID
    retrieved_one = registry.get_scenario("scenario_one")
    retrieved_two = registry.get_scenario("scenario_two")
    retrieved_three = registry.get_scenario("scenario_three")

    # Verify that the retrieved classes are the same as the original ones
    assert retrieved_one is ScenarioOne
    assert retrieved_two is ScenarioTwo
    assert retrieved_three is ScenarioThree

    # Verify the scenario_id is correctly set
    assert retrieved_one.scenario_id == "scenario_one"
    assert retrieved_two.scenario_id == "scenario_two"
    assert retrieved_three.scenario_id == "scenario_three"

    # Create instances and verify they have the correct scenario_id
    instance_one = retrieved_one()
    instance_two = retrieved_two()
    instance_three = retrieved_three()

    assert instance_one.scenario_id == "scenario_one"
    assert instance_two.scenario_id == "scenario_two"
    assert instance_three.scenario_id == "scenario_three"

    # Verify that the instances have the correct class attributes
    assert instance_one.description == "First test scenario"
    assert instance_two.description == "Second test scenario"
    assert instance_three.description == "Third test scenario"

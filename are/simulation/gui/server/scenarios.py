# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


from functools import cache
from typing import Callable

from are.simulation.scenarios.scenario import Scenario
from are.simulation.scenarios.utils.load_utils import load_hf_demo_universes
from are.simulation.scenarios.utils.registry import registry


@cache
def get_gui_scenarios() -> dict[str, Callable[[], Scenario]]:
    """
    Get all GUI scenarios, loading them lazily on first access.

    This function ensures that HuggingFace scenarios are only loaded when
    actually needed, avoiding slow network calls at import time.
    """
    # Get all scenarios from the registry
    # Create lambdas with default arguments to properly capture the scenario
    # class at definition time
    gui_scenarios: dict[str, Callable[[], Scenario]] = {
        scenario_id: lambda sc=scenario_class: sc()
        for scenario_id, scenario_class in registry.get_all_scenarios().items()
    }

    annotator_scenarios = load_hf_demo_universes()
    gui_scenarios.update(annotator_scenarios)

    return gui_scenarios


# For backward compatibility, provide a property-like access
# This will be populated lazily when first accessed
class _LazyGUIScenarios:
    def __getitem__(self, key: str) -> Callable[[], Scenario]:
        return get_gui_scenarios()[key]

    def __contains__(self, key: str) -> bool:
        return key in get_gui_scenarios()

    def __iter__(self):
        return iter(get_gui_scenarios())

    def keys(self):
        return get_gui_scenarios().keys()

    def values(self):
        return get_gui_scenarios().values()

    def items(self):
        return get_gui_scenarios().items()

    def get(self, key: str, default=None):
        return get_gui_scenarios().get(key, default)

    def update(self, other):
        # This shouldn't be used after the lazy loading pattern, but keeping
        # for compatibility
        scenarios = get_gui_scenarios()
        scenarios.update(other)
        # Clear the cache to force reload on next access
        get_gui_scenarios.cache_clear()


GUI_SCENARIOS = _LazyGUIScenarios()

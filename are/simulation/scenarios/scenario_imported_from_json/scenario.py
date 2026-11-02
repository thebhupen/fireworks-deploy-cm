# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import datetime
import logging
from typing import Any

from fsspec import AbstractFileSystem

from are.simulation.apps import ALL_APPS
from are.simulation.scenarios.scenario import Scenario, ScenarioStatus
from are.simulation.types import CapabilityTag, ExecutionMetadata

logger = logging.getLogger(__name__)


def get_apps(
    apps_metadata,
    apps_to_skip: list[str] | None = None,
    apps_to_keep: list[str] | None = None,
    sandbox_dir: str | None = None,
):
    initial_apps = []
    app_class_mapping = {cls.__name__: cls for cls in ALL_APPS}

    for app_data in apps_metadata:
        app_name = app_data.name

        if (
            apps_to_skip
            and app_name in apps_to_skip
            or apps_to_keep
            and app_name not in apps_to_keep
        ):
            logger.debug(f"Skipping loading app {app_name}.")
            continue

        # There could be 2 apps of the same class but different names
        app_class_name = app_data.class_name
        app_state = app_data.app_state
        app_class = app_class_mapping.get(app_class_name or app_name)
        if not app_class:
            logger.error(f"No class found for the app name {app_name}.")
            continue
        if app_class_name and app_class_name != app_name:
            app_instance = (
                app_class(sandbox_dir=sandbox_dir, name=app_name)
                if issubclass(app_class, AbstractFileSystem)
                else app_class(name=app_name)
            )
        else:
            app_instance = (
                app_class(sandbox_dir=sandbox_dir)
                if issubclass(app_class, AbstractFileSystem)
                else app_class()
            )
        logger.debug(f"Created new instance of {app_class}.")
        try:
            app_instance.load_state(app_state)  # type: ignore
            initial_apps.append(app_instance)
        except Exception as e:
            logger.exception(
                f"An error occurred while loading state for {app_name}: {e}"
            )

    return initial_apps


class ScenarioImportedFromJson(Scenario):
    """
    This is a special class used for importing scenarios from JSON files.
    """

    # ID will be overridden upon import.
    scenario_id: str = "scenario_imported_from_json"
    tags: tuple[CapabilityTag, ...] = ()
    start_time: float | None = datetime.datetime.now().timestamp()
    duration: float | None = 1000  # Scenario duration in seconds
    serialized_events: Any = None
    serialized_apps: Any = None
    apps_to_skip: list[str] | None = None
    apps_to_keep: list[str] | None = None
    hints: Any = None
    status: ScenarioStatus = ScenarioStatus.Draft
    execution_metadata: ExecutionMetadata | None = None

    # New fields added to support ExportedTraceDefinitionMetadata
    config: str | None = None
    has_a2a_augmentation: bool = False
    has_tool_augmentation: bool = False
    has_env_events_augmentation: bool = False
    has_exception: bool = False
    exception_type: str | None = None
    exception_message: str | None = None

    def build_events_flow(self) -> None:
        if self.serialized_events:
            self.events = []  # type: ignore
            self.process_events(self.serialized_events)

    def init_and_populate_apps(self, *args, **kwargs) -> None:
        """
        Initialize the apps that will be used in the Scenario.
        """
        self.apps = get_apps(
            apps_metadata=self.serialized_apps,
            apps_to_skip=self.apps_to_skip,
            apps_to_keep=self.apps_to_keep,
            sandbox_dir=kwargs.get("sandbox_dir", None),
        )


if __name__ == "__main__":
    from are.simulation.scenarios.utils.cli_utils import run_and_validate

    run_and_validate(ScenarioImportedFromJson())

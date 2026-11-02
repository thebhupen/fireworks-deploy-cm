# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import datetime
import json
import logging
import os
from typing import Any

from dotenv import load_dotenv

from are.simulation.apps.mcp.mcp_app import MCPApp
from are.simulation.data_handler.importer import JsonScenarioImporter
from are.simulation.scenarios.scenario import Scenario
from are.simulation.scenarios.utils.env_utils import expand_env_vars
from are.simulation.scenarios.utils.load_utils import (
    HF_DEMO_CONFIG,
    HF_DEMO_DATASET_NAME,
    HF_DEMO_SPLIT,
)
from are.simulation.scenarios.utils.registry import register_scenario
from are.simulation.utils.huggingface import get_scenario_from_huggingface

# Set up logger
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

HF_DEMO_UNIVERSE = os.environ.get("HF_DEMO_UNIVERSE", "universe_hf_0")


@register_scenario("scenario_hf_demo_mcp")
class ScenarioHuggingFaceDemoMCP(Scenario):
    """
    Loads the HuggingFace demo universe and populate it with
    extra MCP apps.
    """

    start_time: float | None = datetime.datetime.now().timestamp()
    duration: float | None = None

    def init_and_populate_apps(self, *args, **kwargs) -> None:
        scenario_data = get_scenario_from_huggingface(
            HF_DEMO_DATASET_NAME,
            HF_DEMO_CONFIG,
            HF_DEMO_SPLIT,
            HF_DEMO_UNIVERSE,
        )
        assert scenario_data is not None, (
            f"Scenario couldn't be loaded from HuggingFace {HF_DEMO_DATASET_NAME}/{HF_DEMO_CONFIG}/{HF_DEMO_SPLIT}/{HF_DEMO_UNIVERSE}"
        )
        scenario_importer = JsonScenarioImporter()
        s, _, _ = scenario_importer.import_from_json(
            scenario_data,
            apps_to_skip=None,
            apps_to_keep=None,
            load_completed_events=False,
        )

        s.init_and_populate_apps(*args, **kwargs)

        # get apps from the demo
        self.apps = s.apps if hasattr(s, "apps") else []

        # form task from universe params
        self.start_time = s.start_time

        # Load additional MCP apps from JSON file if specified
        self._load_mcp_apps_from_json()

    def _load_mcp_apps_from_json(self) -> None:
        """
        Load additional MCP apps from a JSON file specified in the environment variables.

        The JSON file should follow the Claude MCP definition format with a ``mcpServers``
        key containing server configurations. Environment variables in the JSON are
        expanded using the current environment.

        :return: None
        """
        # Get the JSON file path from environment variables
        mcp_apps_json_path = os.environ.get("MCP_APPS_JSON_PATH")

        if not mcp_apps_json_path:
            return

        # Ensure self.apps is initialized
        if not hasattr(self, "apps") or self.apps is None:
            self.apps = []

        try:
            with open(mcp_apps_json_path, "r") as f:
                mcp_config = json.load(f)

            if "mcpServers" not in mcp_config:
                logger.warning(
                    f"No 'mcpServers' key found in MCP apps JSON file: {mcp_apps_json_path}"
                )
                return

            # Create MCP apps from the JSON configuration
            for server_name, server_config in mcp_config["mcpServers"].items():
                mcp_app = self._create_mcp_app(server_name, server_config)
                if mcp_app:
                    self.apps.append(mcp_app)
                    logger.info(f"Added MCP app: {server_name}")

        except Exception as e:
            logger.error(f"Error loading MCP apps from JSON: {e}", exc_info=True)

    def _create_mcp_app(self, name: str, config: dict[str, Any]) -> MCPApp | None:
        """
        Create an MCPApp instance from a server configuration.

        Supports two types of MCP servers:

        1. Local servers with command and arguments
        2. Remote SSE servers with URL and headers

        Environment variables in the configuration are expanded before creating the app.

        :param name: The name of the MCP app
        :type name: str
        :param config: The server configuration from the JSON file
        :type config: dict[str, Any]
        :return: An MCPApp instance or None if creation fails
        :rtype: MCPApp | None
        """
        try:
            # Expand environment variables in the configuration
            expanded_config = expand_env_vars(config, allowed=["HF_TOKEN"])

            # Handle SSE remote servers
            if expanded_config.get("type") == "sse" or "url" in expanded_config:
                return MCPApp(
                    name=name,
                    server_url=expanded_config.get("url"),
                    sse_headers=expanded_config.get("headers", {}),
                )

            # Handle local servers with command and args
            elif "command" in expanded_config:
                return MCPApp(
                    name=name,
                    server_command=expanded_config.get("command"),
                    server_args=expanded_config.get("args", []),
                    server_env=expanded_config.get("env", {}),
                )

            else:
                logger.warning(f"Unsupported MCP server configuration for {name}")
                return None

        except Exception as e:
            logger.error(f"Error creating MCP app {name}: {e}", exc_info=True)
            return None


if __name__ == "__main__":
    from are.simulation.scenarios.utils.cli_utils import run_and_validate

    run_and_validate(ScenarioHuggingFaceDemoMCP())

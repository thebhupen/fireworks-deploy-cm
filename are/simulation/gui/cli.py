# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import logging
import os
import signal
import sys
import threading
from cProfile import Profile

import click

from are.simulation.cli.shared_params import common_options, kwargs_option
from are.simulation.cli.utils import parse_json_safely, setup_logging
from are.simulation.gui.server.graphql.query import Query
from are.simulation.gui.server.graphql.schema import Mutation
from are.simulation.gui.server.graphql.subscription import Subscription
from are.simulation.gui.server.scenarios import GUI_SCENARIOS
from are.simulation.gui.server.server import ARESimulationGuiServer
from are.simulation.notification_system import VerboseNotificationSystem
from are.simulation.utils.huggingface import parse_huggingface_url

server: ARESimulationGuiServer | None = None
profiler: Profile | None = None
shutdown_event = threading.Event()


@click.command()
@common_options()
@kwargs_option()
@click.option(
    "-s",
    "--scenario_id",
    type=str,
    required=False,
    help="Scenario to run. Can be a scenario ID from the registry or a HuggingFace URL in format: hf://datasets/dataset_name/config/split/scenario_id",
)
@click.option(
    "-h",
    "--hostname",
    type=str,
    required=False,
    default=os.environ.get("ARE_SIMULATION_SERVER_HOSTNAME", "localhost"),
    help="Server hostname",
)
@click.option(
    "-p",
    "--port",
    type=int,
    required=False,
    default=int(os.environ.get("ARE_SIMULATION_SERVER_PORT", 8080)),
    help="Server port",
)
@click.option(
    "-c",
    "--certfile",
    type=str,
    required=False,
    default=os.environ.get("ARE_SIMULATION_SSL_CERT_PATH", ""),
    help="Server SSL certificate path",
)
@click.option(
    "-k",
    "--keyfile",
    type=str,
    required=False,
    default=os.environ.get("ARE_SIMULATION_SSL_KEY_PATH", ""),
    help="Server SSL key path",
)
@click.option("-d", "--debug", is_flag=True, help="Enable debugging mode.")
@click.option("--profile", is_flag=True, help="Enable cProfile profiler.")
@click.option(
    "--ui_view",
    type=str,
    required=False,
    help="Default UI mode to start client in. Examples: 'SCENARIOS', 'PLAYGROUND'",
)
@click.option(
    "--inactivity-limit",
    type=int,
    required=False,
    default=int(os.environ.get("ARE_SIMULATION_INACTIVITY_LIMIT", 3600)),
    help="Session inactivity limit in seconds before cleanup",
)
@click.option(
    "--cleanup-interval",
    type=int,
    required=False,
    default=int(os.environ.get("ARE_SIMULATION_CLEANUP_INTERVAL", 300)),
    help="Interval in seconds between session cleanup checks",
)
@click.option(
    "--dataset-path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    required=False,
    help="Path to the dataset directory containing JSON scenario files organized in subfolders",
)
def main(
    model: str,
    provider: str | None = None,
    endpoint: str | None = None,
    agent: str | None = None,
    log_level: str = "INFO",
    kwargs: str = "{}",
    scenario_id: str | None = None,
    hostname: str = "localhost",
    port: int = 8080,
    certfile: str = "",
    keyfile: str = "",
    debug: bool = False,
    profile: bool = False,
    ui_view: str | None = None,
    inactivity_limit: int = 3600,
    cleanup_interval: int = 300,
    dataset_path: str | None = None,
):
    """
    Main entry point for the Meta Agents Research Environments GUI server CLI.

    This function starts the Meta Agents Research Environments GUI server with the specified configuration,
    providing a web-based interface for running and managing scenarios.
    """
    # Set up logging
    setup_logging(log_level)

    # Parse the kwargs JSON string into a dictionary
    kwargs_dict = parse_json_safely(kwargs, "kwargs")

    # Validate scenario_id
    if scenario_id is not None:
        hf_params = parse_huggingface_url(scenario_id)
        if hf_params is None and scenario_id not in GUI_SCENARIOS:
            raise click.UsageError(
                f"Invalid scenario_id '{scenario_id}'. Must be either:\n"
                f"  - A scenario ID from the registry: {', '.join(list(GUI_SCENARIOS.keys())[:5])}...\n"
                f"  - A HuggingFace URL in format: hf://datasets/dataset_name/config/split/scenario_id"
            )

    global server
    server = ARESimulationGuiServer(
        hostname=hostname,
        port=port,
        certfile=certfile,
        keyfile=keyfile,
        debug=debug,
        scenario_id=scenario_id,
        scenario_args=kwargs_dict,
        agent=agent,
        model=model,
        provider=provider,
        endpoint=endpoint,
        default_ui_view=ui_view,
        inactivity_limit=inactivity_limit,
        cleanup_interval=cleanup_interval,
        dataset_path=dataset_path,
        notification_system_builder=VerboseNotificationSystem,
    )

    Query.server = server  # type: ignore[reportAttributeAccessIssue]
    Mutation.server = server  # type: ignore[reportAttributeAccessIssue]
    Subscription.server = server  # type: ignore[reportAttributeAccessIssue]

    def clean_exit(sig=None, frame=None):
        print("\nShutting down gracefully...")
        if profiler is not None:
            profiler.disable()
            profiler.dump_stats("are.simulation.cprofile")

        if server is not None:
            server.stop()

        shutdown_event.set()
        sys.exit(0)

    # Cross-platform signal handling
    def setup_signal_handlers():
        try:
            # Handle SIGINT (Ctrl+C)
            signal.signal(signal.SIGINT, clean_exit)

            # Handle SIGTERM for graceful shutdown
            if hasattr(signal, "SIGTERM"):
                signal.signal(signal.SIGTERM, clean_exit)

            # On Windows, also handle SIGBREAK (Ctrl+Break)
            if sys.platform == "win32":
                if hasattr(signal, "SIGBREAK"):
                    signal.signal(signal.SIGBREAK, clean_exit)

        except (OSError, ValueError) as e:
            # Some signals might not be available on all platforms
            logging.warning(f"Could not set up signal handler: {e}")

    setup_signal_handlers()

    # On Windows, set up keyboard interrupt monitor thread
    if sys.platform == "win32":

        def keyboard_interrupt_monitor():
            try:
                while not shutdown_event.is_set():
                    # Check for keyboard interrupt every 100ms
                    shutdown_event.wait(0.1)
            except KeyboardInterrupt:
                clean_exit()

        monitor_thread = threading.Thread(
            target=keyboard_interrupt_monitor, daemon=True
        )
        monitor_thread.start()

    if profile:
        global profiler
        profiler = Profile()
        profiler.enable()

    try:
        server.run()
    except KeyboardInterrupt:
        clean_exit()


# To run in Conda environment, use e.g., `python -m are.simulation.gui.cli -s scenario_find_image_file`
if __name__ == "__main__":
    main()

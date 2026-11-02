# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import logging
import os
import uuid
from threading import Lock
from typing import Any, Callable

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.routing import Route
from strawberry.fastapi import GraphQLRouter

from are.simulation.agents.agent_builder import AbstractAgentBuilder, AgentBuilder
from are.simulation.agents.agent_config_builder import (
    AbstractAgentConfigBuilder,
    AgentConfigBuilder,
)
from are.simulation.config import ARE_SIMULATION_ROOT, ARE_SIMULATION_SANDBOX_PATH
from are.simulation.gui.server.are_simulation_gui import ARESimulationGui
from are.simulation.gui.server.constants import FILES_PATH, UI_PATH
from are.simulation.gui.server.graphql.schema import schema
from are.simulation.gui.server.session_manager import SessionManager
from are.simulation.notification_system import BaseNotificationSystem

logger = logging.getLogger(__name__)


# Monkeypatch to not cache static resources.
# This helps prevent stale UI when deploying changes.
StaticFiles.is_not_modified = lambda self, *args, **kwargs: False


def create_frontend_route():
    build_path = ARE_SIMULATION_ROOT / "simulation/gui/client/build"

    if not build_path.is_dir() or not (build_path / "index.html").is_file():
        logger.warning(
            f"Frontend build directory not found or incomplete at {build_path}. Serving frontend will likely fail."
        )

        async def missing_frontend(request):
            return Response(
                "Frontend not built.",
                media_type="text/plain",
                status_code=503,
            )

        return Route("/{path:path}", endpoint=missing_frontend)

    return StaticFiles(directory=build_path, html=True, check_dir=False)


class ARESimulationGuiServer:
    def __init__(
        self,
        hostname: str,
        port: int,
        certfile: str,
        keyfile: str,
        debug: bool,
        scenario_id: str | None,
        scenario_args: dict[str, Any] = {},
        agent: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        endpoint: str | None = None,
        agent_config_builder: AbstractAgentConfigBuilder | None = None,
        agent_builder: AbstractAgentBuilder | None = None,
        default_ui_view: str | None = None,
        inactivity_limit: int = 3600,
        cleanup_interval: int = 300,
        notification_system_builder: Callable[[], BaseNotificationSystem] | None = None,
        dataset_path: str | None = None,
    ):
        # Setup FastAPI.
        self.app = FastAPI()
        self.app.include_router(
            GraphQLRouter(
                schema=schema,
                graphql_ide=None,
            ),
            prefix="/graphql",
        )
        # Mount frontend with fallback
        self.app.mount(UI_PATH, create_frontend_route(), name="frontend")

        os.makedirs(ARE_SIMULATION_SANDBOX_PATH, exist_ok=True)
        self.app.mount(
            FILES_PATH,
            StaticFiles(directory=ARE_SIMULATION_SANDBOX_PATH, check_dir=True),
            name="files",
        )
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )
        # Error handler.
        self.app.add_exception_handler(Exception, self.handle_error)

        async def read_root():
            return RedirectResponse(url=UI_PATH)

        self.app.add_api_route("/", read_root, methods=["GET"])

        async def health_check():
            return JSONResponse(status_code=200, content={"status": "OK"})

        self.app.add_api_route("/health", health_check, methods=["GET"])

        async def get_sessions():
            return JSONResponse(
                status_code=200,
                content={"sessions": self.session_manager.get_status()},
            )

        self.app.add_api_route("/sessions", get_sessions, methods=["GET"])

        self.hostname = hostname
        self.port = port
        self.certfile = certfile
        self.keyfile = keyfile

        # Parameters to create are.simulation gui instance.
        self.scenario_id: str | None = scenario_id
        self.scenario_args: dict[str, Any] = scenario_args
        self.agent: str | None = agent
        self.model: str | None = model
        self.provider: str | None = provider
        self.endpoint: str | None = endpoint
        self.agent_config_builder: AbstractAgentConfigBuilder = (
            agent_config_builder
            if agent_config_builder is not None
            else AgentConfigBuilder()
        )
        self.agent_builder: AbstractAgentBuilder = (
            agent_builder if agent_builder is not None else AgentBuilder()
        )
        self.default_ui_view: str | None = default_ui_view
        self.notification_system_builder: (
            Callable[[], BaseNotificationSystem] | None
        ) = notification_system_builder
        self.dataset_path: str | None = dataset_path

        # Lock for thread safety
        self.lock = Lock()

        # Initialize SessionManager.
        self.session_manager = SessionManager(inactivity_limit, cleanup_interval)
        # There is no open implementation for db manager.
        self.db_manager = None

        self.server_id = self.get_ecs_task_id() or str(uuid.uuid1())[:8]
        self.server_version = os.getenv("ARE_SIMULATION_SERVER_VERSION", "dev")

        # Start debugger if requested.
        if debug:
            self._wait_for_debugger()

    def get_ecs_task_id(self):
        try:
            metadata_uri = os.getenv("ECS_CONTAINER_METADATA_URI_V4")
            if metadata_uri:
                task_id = metadata_uri.split("/")[-1]
                return task_id
            else:
                return None
        except Exception as e:
            logger.exception(f"Failed to retrieve ECS Task id: {e}")
            return None

    def handle_error(self, request: Request, e: Exception):
        logger.error(f"Error in ARESimulationGuiServer: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)},
        )

    def get_all_agents(self) -> list[str]:
        return self.agent_builder.list_agents() if self.agent_builder else []

    def get_default_ui_view(self) -> str | None:
        return self.default_ui_view.upper() if self.default_ui_view else None

    def get_or_create_are_simulation(self, session_id: str) -> ARESimulationGui:
        if self.session_manager.session_exists(session_id):
            return self.session_manager.get_are_simulation_instance(session_id)

        with self.lock:
            if self.session_manager.session_exists(session_id):
                return self.session_manager.get_are_simulation_instance(session_id)

            are_simulation_instance = ARESimulationGui(
                session_id=session_id,
                scenario_id=self.scenario_id,
                scenario_args=self.scenario_args,
                agent_config_builder=self.agent_config_builder,
                agent_builder=self.agent_builder,
                default_agent_name=self.agent,
                default_model_name=self.model,
                default_provider=self.provider,
                default_endpoint=self.endpoint,
                notification_system_builder=self.notification_system_builder,
                db_manager=self.db_manager,
                dataset_path=self.dataset_path,
            )
            self.session_manager.add_are_simulation_instance(
                session_id, are_simulation_instance
            )
            logger.info(
                f"Created new ARESimulationGui instance for {session_id}. Total: {self.session_manager.get_total_sessions()}."
            )
            return are_simulation_instance

    def run(self):
        # Handle the are.simulation run through the GraphQL mutation
        self.session_manager.start()
        self._run_uvicorn()

    def _run_uvicorn(self) -> None:
        protocol = "https" if self.certfile and self.keyfile else "http"
        logger.info(f"Access your server at {protocol}://{self.hostname}:{self.port}")

        uvicorn.run(
            app=self.app,
            host=self.hostname,
            port=self.port,
            ssl_certfile=self.certfile,
            ssl_keyfile=self.keyfile,
            reload=False,
            log_level="warning",
        )

    def stop(self):
        self.session_manager.stop()

    def _wait_for_debugger(self):
        import debugpy

        port = 5678
        logger.info(f"Waiting for debugger on port {port}...")
        debugpy.listen(port)
        debugpy.wait_for_client()
        debugpy.breakpoint()

# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import logging
import time
from dataclasses import dataclass, field
from threading import Thread

from are.simulation.gui.server.are_simulation_gui import ARESimulationGui

logger = logging.getLogger(__name__)


@dataclass
class Session:
    are_simulation_instance: ARESimulationGui
    last_active: float = field(default_factory=time.time)

    def update_last_active(self) -> None:
        """Update the last active time of the session."""
        self.last_active = time.time()


class SessionManager:
    def __init__(self, inactivity_limit: int, cleanup_interval: int):
        self.sessions: dict[str, Session] = {}
        self.inactivity_limit = inactivity_limit
        self.cleanup_interval = cleanup_interval
        self.cleanup_timer: Thread | None = None
        self.keep_cleanup = False

    def get_are_simulation_instance(self, session_id: str) -> ARESimulationGui:
        """Retrieve a ARESimulationGui instance by session ID."""
        session = self.sessions.get(session_id)
        if session is None:
            raise ValueError(f"Session {session_id} does not exist.")

        session.update_last_active()
        return session.are_simulation_instance

    def add_are_simulation_instance(
        self, session_id: str, are_simulation_instance: ARESimulationGui
    ) -> None:
        """Add a ARESimulationGui instance to the session manager."""
        self.sessions[session_id] = Session(
            are_simulation_instance=are_simulation_instance
        )

    def session_exists(self, session_id: str) -> bool:
        """Check if a session exists."""
        return session_id in self.sessions

    def get_total_sessions(self) -> int:
        """Return the total number of active sessions."""
        return len(self.sessions)

    def get_status(self) -> dict[str, float]:
        """Return the status of all active sessions."""
        return {
            session_id: session.last_active
            for session_id, session in self.sessions.items()
        }

    def start(self) -> None:
        """Start the session manager."""
        self._start_cleanup_timer()

    def stop(self) -> None:
        """Stop the session manager and all active sessions."""
        for session in self.sessions.values():
            session.are_simulation_instance.stop()
        self._stop_cleanup_timer()

    def _start_cleanup_timer(self):
        self.cleanup_timer = Thread(target=self._cleanup_routine, name="SessionManager")
        self.keep_cleanup = True
        self.cleanup_timer.start()

    def _stop_cleanup_timer(self):
        self.keep_cleanup = False
        if self.cleanup_timer is not None and self.cleanup_timer.is_alive():
            self.cleanup_timer.join()

    def _cleanup_routine(self) -> None:
        while (
            self.keep_cleanup
            and self.cleanup_timer is not None
            and self.cleanup_timer.is_alive()
        ):
            logger.info("Checking for inactive are_simulation instances.")
            self._cleanup_inactive_are_simulation()
            cleanup_wait_started = time.time()
            while (
                self.keep_cleanup
                and self.cleanup_timer is not None
                and self.cleanup_timer.is_alive()
                and time.time() - cleanup_wait_started < self.cleanup_interval
            ):
                time.sleep(1)

    def _cleanup_inactive_are_simulation(self):
        current_time = time.time()
        inactive_sessions = [
            session_id
            for session_id, session in self.sessions.items()
            if current_time - session.last_active > self.inactivity_limit
        ]
        for session_id in inactive_sessions:
            if session_id in self.sessions:
                self.sessions[session_id].are_simulation_instance.stop()
                del self.sessions[session_id]
                logger.info(
                    f"Cleaned up inactive ARESimulationGui instance for session: {session_id}"
                )

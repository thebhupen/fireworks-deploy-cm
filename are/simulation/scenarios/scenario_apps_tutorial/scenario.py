# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


"""
App Implementation Tutorial

This tutorial demonstrates how to implement a custom app in Meta Agents Research Environments using the ContactsApp as an example.
It covers the essential components of app development including:
- Data models and validation
- App class structure and inheritance
- Tool decorators and method registration
- State management and persistence
- Event handling and integration

The tutorial creates a simplified version of a contacts app to illustrate key concepts.
"""

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from are.simulation.apps.agent_user_interface import AgentUserInterface
from are.simulation.apps.app import App
from are.simulation.apps.contacts import Contact, ContactsApp, Gender, Status
from are.simulation.scenarios.scenario import Scenario, ScenarioValidationResult
from are.simulation.scenarios.utils.registry import register_scenario
from are.simulation.tool_utils import OperationType, app_tool, data_tool
from are.simulation.types import EventRegisterer, event_registered
from are.simulation.utils import get_state_dict, type_check

# Step 1: Define Data Models
# =========================


class Priority(Enum):
    """Priority levels for tasks - demonstrates enum usage in data models"""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    URGENT = "Urgent"


@dataclass
class Task:
    """
    A simple task data model demonstrating key patterns:
    - Required and optional fields
    - Default value generation (UUID)
    - Enum usage for constrained values
    - Validation in __post_init__
    """

    title: str
    description: str = ""
    task_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    priority: Priority = Priority.MEDIUM
    completed: bool = False

    def __post_init__(self):
        """Validate data after initialization - critical for data integrity"""
        if not self.title or len(self.title.strip()) == 0:
            raise ValueError("Task title cannot be empty")

        # Handle string-to-enum conversion for flexibility
        if isinstance(self.priority, str):
            try:
                self.priority = Priority(self.priority)
            except ValueError:
                raise ValueError(f"Invalid priority: {self.priority}")

    def __str__(self):
        """String representation for debugging and display"""
        status = "✓" if self.completed else "○"
        return f"{status} [{self.priority.value}] {self.title}"


# Step 2: Implement the App Class
# ===============================
# Apps inherit from the base App class and manage application state and behavior.


@dataclass
class SimpleTaskApp(App):
    """
    A simple task management app demonstrating core app implementation patterns.

    Key Features Demonstrated:
    - Data storage and management
    - Tool method registration with decorators
    - State persistence and loading
    - Type checking and validation
    - Event registration for environment integration

    This app manages a collection of tasks with basic CRUD operations.
    """

    # App-specific configuration
    name: str | None = "SimpleTaskApp"
    tasks: dict[str, Task] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize the app - always call super().__init__()"""
        super().__init__(self.name)

    # Step 3: State Management
    # =======================
    # Apps must implement state persistence for scenario reproducibility

    def get_state(self) -> dict[str, Any]:
        """
        Return the app's current state for persistence.
        Use get_state_dict utility for consistent serialization.
        """
        return get_state_dict(self, ["tasks"])

    def load_state(self, state_dict: dict[str, Any]):
        """
        Restore app state from saved data.
        Handle data conversion and validation carefully.
        """
        self.tasks = {}
        tasks_data = state_dict.get("tasks", {})

        for task_id, task_data in tasks_data.items():
            # Reconstruct Task objects from saved data
            task = Task(
                title=task_data["title"],
                description=task_data.get("description", ""),
                task_id=task_data.get("task_id", task_id),
                priority=Priority(task_data.get("priority", "Medium")),
                completed=task_data.get("completed", False),
            )
            self.tasks[task_id] = task

    def reset(self):
        """Reset app to initial state - important for scenario repeatability"""
        super().reset()
        self.tasks = {}

    # Step 4: Tool Methods - The Core Functionality
    # ============================================
    # Tool methods are the primary interface between agents and your app.
    # Use decorators to register methods as tools with proper metadata.

    @type_check  # Validates parameter types at runtime
    @app_tool()  # Registers method as an agent-accessible tool
    @data_tool()  # Marks as a data access tool (for analytics)
    @event_registered()  # Registers events for environment tracking
    def create_task(
        self, title: str, description: str = "", priority: str = "Medium"
    ) -> str:
        """
        Create a new task in the task management system.

        :param title: The title of the task (required)
        :param description: Optional description of the task
        :param priority: Priority level (Low, Medium, High, Urgent)
        :returns: The unique task_id of the created task
        """
        # Create and validate the task
        task = Task(title=title, description=description, priority=Priority(priority))

        # Store the task
        self.tasks[task.task_id] = task

        return task.task_id

    @type_check
    @app_tool()
    @data_tool()
    @event_registered(operation_type=OperationType.READ)  # Mark as read operation
    def get_tasks(self, completed_only: bool = False) -> list[dict[str, Any]]:
        """
        Retrieve all tasks, optionally filtered by completion status.

        :param completed_only: If True, return only completed tasks
        :returns: List of task dictionaries with all task information
        """
        tasks = list(self.tasks.values())

        if completed_only:
            tasks = [task for task in tasks if task.completed]

        # Return serializable data (not objects)
        return [
            {
                "task_id": task.task_id,
                "title": task.title,
                "description": task.description,
                "priority": task.priority.value,
                "completed": task.completed,
            }
            for task in tasks
        ]

    @type_check
    @app_tool()
    @data_tool()
    @event_registered()
    def get_task(self, task_id: str) -> dict[str, Any]:
        """
        Retrieve a specific task by its ID.

        :param task_id: The unique identifier of the task
        :returns: Task information as a dictionary
        """
        if task_id not in self.tasks:
            raise KeyError(f"Task {task_id} does not exist")

        task = self.tasks[task_id]
        return {
            "task_id": task.task_id,
            "title": task.title,
            "description": task.description,
            "priority": task.priority.value,
            "completed": task.completed,
        }

    @type_check
    @app_tool()
    @data_tool()
    @event_registered(operation_type=OperationType.WRITE)  # Mark as write operation
    def complete_task(self, task_id: str) -> str:
        """
        Mark a task as completed.

        :param task_id: The unique identifier of the task to complete
        :returns: Success message
        """
        if task_id not in self.tasks:
            raise KeyError(f"Task {task_id} does not exist")

        self.tasks[task_id].completed = True
        return f"Task {task_id} marked as completed"

    @type_check
    @app_tool()
    @data_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def update_task(
        self,
        task_id: str,
        title: str | None = None,
        description: str | None = None,
        priority: str | None = None,
    ) -> str:
        """
        Update an existing task's properties.

        :param task_id: The unique identifier of the task to update
        :param title: New title for the task (optional)
        :param description: New description for the task (optional)
        :param priority: New priority level (optional)
        :returns: Success message
        """
        if task_id not in self.tasks:
            raise KeyError(f"Task {task_id} does not exist")

        task = self.tasks[task_id]

        # Update only provided fields
        if title is not None:
            if not title.strip():
                raise ValueError("Task title cannot be empty")
            task.title = title

        if description is not None:
            task.description = description

        if priority is not None:
            task.priority = Priority(priority)

        return f"Task {task_id} updated successfully"

    @type_check
    @app_tool()
    @data_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def delete_task(self, task_id: str) -> str:
        """
        Delete a task from the system.

        :param task_id: The unique identifier of the task to delete
        :returns: Success message
        """
        if task_id not in self.tasks:
            raise KeyError(f"Task {task_id} does not exist")

        del self.tasks[task_id]
        return f"Task {task_id} deleted successfully"


# Step 5: Create a Tutorial Scenario
# ==================================
# Scenarios demonstrate how your app integrates with the Meta Agents Research Environments environment


@register_scenario("scenario_apps_tutorial")
class ScenarioAppsTutorial(Scenario):
    """
    Tutorial scenario demonstrating app implementation concepts.

    This scenario shows:
    - App initialization and population
    - Event creation and scheduling
    - Agent interaction with custom apps
    - Validation of app behavior
    """

    start_time: float | None = 0
    duration: float | None = 30

    def init_and_populate_apps(self, *args, **kwargs) -> None:
        """Initialize apps and populate with sample data"""

        # Initialize our custom app
        task_app = SimpleTaskApp()

        # Initialize other required apps
        agui = AgentUserInterface()
        contacts = ContactsApp()

        # Populate with sample data to create realistic scenarios
        # Add some initial tasks
        task_app.create_task(
            title="Review quarterly reports",
            description="Analyze Q3 financial performance and prepare summary",
            priority="High",
        )

        self.team_meeting_id = task_app.create_task(
            title="Schedule team meeting",
            description="Coordinate with all team members for next week",
            priority="Medium",
        )

        # Add sample contacts for integration testing
        contacts.add_contact(
            Contact(
                first_name="Alice",
                last_name="Johnson",
                email="alice.johnson@company.com",
                phone="+1-555-0123",
                gender=Gender.FEMALE,
                status=Status.EMPLOYED,
            )
        )

        # Store apps for scenario use
        self.apps = [task_app, agui, contacts]

    def build_events_flow(self) -> None:
        """Define the sequence of events that will occur during the scenario"""

        agui = self.get_typed_app(AgentUserInterface)
        task_app = self.get_typed_app(SimpleTaskApp)

        with EventRegisterer.capture_mode():
            # User event: User requests task creation
            event1 = agui.send_message_to_agent(
                content="Please create a new high-priority task titled 'Prepare presentation' with description 'Create slides for the upcoming client meeting'. Also, mark the 'Schedule team meeting' task as completed",
            ).depends_on(None, delay_seconds=2)
            # Oracle event 1: Agent creates the presentation task
            oracle1 = (
                task_app.create_task(
                    title="Prepare presentation",
                    description="Create slides for the upcoming client meeting",
                    priority="High",
                )
                .oracle()
                .depends_on(event1, delay_seconds=2)
            )

            # Oracle event 2: Agent marks the team meeting task as completed
            oracle2 = (
                task_app.complete_task(task_id=self.team_meeting_id)
                .oracle()
                .depends_on(oracle1, delay_seconds=5)
            )

        self.events = [event1, oracle1, oracle2]

    def validate(self, env) -> ScenarioValidationResult:
        """
        Validate that the scenario completed successfully.

        Check that the agent properly interacted with our custom app.
        """
        try:
            task_app = env.get_app("SimpleTaskApp")

            # Validation 1: Check that a new task was created
            tasks = list(task_app.tasks.values())
            presentation_task = None
            for task in tasks:
                if "presentation" in task.title.lower():
                    presentation_task = task
                    break

            if not presentation_task:
                return ScenarioValidationResult(
                    success=False,
                    exception=Exception(
                        "Agent did not create the requested presentation task"
                    ),
                )

            # Validation 2: Check that the presentation task has correct priority
            if presentation_task.priority != Priority.HIGH:
                return ScenarioValidationResult(
                    success=False,
                    exception=Exception(
                        "Presentation task does not have high priority"
                    ),
                )

            # Validation 3: Check that the team meeting task was completed
            meeting_task = None
            for task in tasks:
                if "meeting" in task.title.lower():
                    meeting_task = task
                    break

            if not meeting_task or not meeting_task.completed:
                return ScenarioValidationResult(
                    success=False,
                    exception=Exception(
                        "Team meeting task was not marked as completed"
                    ),
                )

            return ScenarioValidationResult(success=True)

        except Exception as e:
            return ScenarioValidationResult(success=False, exception=e)


if __name__ == "__main__":
    from are.simulation.scenarios.utils.cli_utils import run_and_validate

    # Run the scenario in oracle mode and validate the agent actions
    run_and_validate(ScenarioAppsTutorial())

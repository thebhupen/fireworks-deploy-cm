#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


"""
Todo tracking MCP server for use with Meta Agents Research Environments MCPApp.

This server provides todo list management operations as MCP tools.
"""

import datetime
import json
from dataclasses import asdict, dataclass, field

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

# Create an MCP server
mcp = FastMCP("Todo Tracking MCP Server")


# Define Todo item as a dataclass
@dataclass
class TodoItem:
    """
    Represents a todo item with its properties.

    :param id: Unique identifier for the todo item
    :param title: Title of the todo item
    :param description: Detailed description of the todo item
    :param created_at: ISO format timestamp of when the item was created
    :param completed: Whether the todo item is completed
    :param completed_at: ISO format timestamp of when the item was completed
    """

    id: str
    title: str
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    completed: bool = False
    completed_at: str | None = None

    def to_dict(self) -> dict:
        """
        Convert the todo item to a dictionary.

        :return: Dictionary representation of the todo item
        """
        return asdict(self)


# Global state for todo tracking
TODO_LIST: dict[str, TodoItem] = {}
TODO_COUNTER = 0


# Todo tracking tools
@mcp.tool(
    annotations=ToolAnnotations(
        title="Add Todo Item",
        readOnlyHint=False,  # This tool modifies server state
        destructiveHint=False,  # It performs additive updates, not destructive ones
        idempotentHint=False,  # Adding the same todo twice creates two entries
        openWorldHint=False,  # Operates within the server's state
    )
)
def add_todo(title: str, description: str = "") -> str:
    """
    Add a new todo item to the list.

    :param title: The title of the todo item
    :param description: Optional detailed description of the todo item
    :return: JSON string of the created todo item with its ID
    """
    global TODO_COUNTER, TODO_LIST
    TODO_COUNTER += 1
    todo_id = str(TODO_COUNTER)

    todo_item = TodoItem(id=todo_id, title=title, description=description)

    TODO_LIST[todo_id] = todo_item
    return json.dumps(todo_item.to_dict(), indent=2)


@mcp.tool(
    annotations=ToolAnnotations(
        title="List Todo Items",
        readOnlyHint=True,  # This tool doesn't modify server state
        idempotentHint=True,  # Always returns the current state
        openWorldHint=False,  # Operates within the server's state
    )
)
def list_todos(include_completed: bool = True) -> str:
    """
    List all todo items.

    :param include_completed: Whether to include completed items in the list
    :return: JSON string containing a list of todo items
    """
    if include_completed:
        todos = [todo.to_dict() for todo in TODO_LIST.values()]
    else:
        todos = [todo.to_dict() for todo in TODO_LIST.values() if not todo.completed]

    return json.dumps(todos, indent=2)


@mcp.tool(
    annotations=ToolAnnotations(
        title="Mark Todo as Completed",
        readOnlyHint=False,  # This tool modifies server state
        destructiveHint=False,  # It updates but doesn't destroy data
        idempotentHint=True,  # Marking as completed multiple times has same effect
        openWorldHint=False,  # Operates within the server's state
    )
)
def complete_todo(todo_id: str) -> str:
    """
    Mark a todo item as completed.

    :param todo_id: The ID of the todo item to mark as completed
    :return: JSON string of the updated todo item
    """
    if todo_id not in TODO_LIST:
        raise ValueError(f"Todo item with ID {todo_id} not found")

    todo_item = TODO_LIST[todo_id]
    todo_item.completed = True
    todo_item.completed_at = datetime.datetime.now().isoformat()

    return json.dumps(todo_item.to_dict(), indent=2)


@mcp.tool(
    annotations=ToolAnnotations(
        title="Delete Todo Item",
        readOnlyHint=False,  # This tool modifies server state
        destructiveHint=True,  # It permanently removes data
        idempotentHint=False,  # Deleting twice will fail the second time
        openWorldHint=False,  # Operates within the server's state
    )
)
def delete_todo(todo_id: str) -> str:
    """
    Delete a todo item from the list.

    :param todo_id: The ID of the todo item to delete
    :return: JSON string of the deleted todo item
    """
    if todo_id not in TODO_LIST:
        raise ValueError(f"Todo item with ID {todo_id} not found")

    deleted_item = TODO_LIST[todo_id]
    del TODO_LIST[todo_id]

    return json.dumps(deleted_item.to_dict(), indent=2)


@mcp.resource("todos://list")
def get_todos_list() -> str:
    """
    Get a list of all todo items.

    :return: JSON string containing a list of all todo items
    """
    todos = [todo.to_dict() for todo in TODO_LIST.values()]
    return json.dumps(todos, indent=2)


@mcp.resource("todos://{todo_id}")
def get_todo_by_id(todo_id: str) -> str:
    """
    Get a specific todo item by ID.

    :param todo_id: The ID of the todo item to retrieve
    :return: JSON string of the requested todo item or error message if not found
    """
    if todo_id not in TODO_LIST:
        return json.dumps({"error": f"Todo item with ID {todo_id} not found"}, indent=2)

    return json.dumps(TODO_LIST[todo_id].to_dict(), indent=2)


@mcp.resource("todos://stats")
def get_todos_stats() -> str:
    """
    Get statistics about todo items.

    :return: JSON string containing statistics about todo items
    """
    total = len(TODO_LIST)
    completed = sum(1 for todo in TODO_LIST.values() if todo.completed)
    active = total - completed

    stats = {
        "total": total,
        "completed": completed,
        "active": active,
        "completion_rate": f"{(completed / total * 100) if total > 0 else 0:.1f}%",
    }

    return json.dumps(stats, indent=2)


@mcp.resource("help://todo")
def get_todo_help() -> str:
    """
    Get help on todo tracking tools.

    :return: String containing help information about todo tracking tools
    """
    return """
Todo Tracking Tools:
- add_todo(title, description=""): Add a new todo item
- list_todos(include_completed=True): List all todo items
- complete_todo(todo_id): Mark a todo item as completed
- delete_todo(todo_id): Delete a todo item
"""


# Run the server if executed directly
if __name__ == "__main__":
    mcp.run()

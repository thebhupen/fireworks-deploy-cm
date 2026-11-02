# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


from typing import Any

from are.simulation.apps.app import App, Protocol
from are.simulation.apps.sandbox_file_system import SandboxLocalFileSystem
from are.simulation.tool_utils import OperationType, app_tool
from are.simulation.types import event_registered


class VirtualFileSystem(App):
    """
    A proxy class that delegates file system operations to SandboxLocalFileSystem.
    This class maintains backward compatibility with the original VirtualFileSystem API
    while using the more comprehensive SandboxLocalFileSystem implementation.
    """

    def __init__(self, name: str | None = None):
        super().__init__(name)
        # Create an instance of SandboxLocalFileSystem to delegate operations to
        self.sandbox_fs = SandboxLocalFileSystem(name)

    def get_implemented_protocols(self) -> list[Protocol]:
        return [Protocol.FILE_SYSTEM]

    def reset(self):
        super().reset()
        self.sandbox_fs.reset()

    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def open(self, path: str, mode: str = "rb"):
        """
        Open a file for reading or writing.
        :param path: path to the file to open
        :param mode: mode to open the file in
        :returns: file handle to the opened file
        """
        return self.sandbox_fs.open(path, mode)

    def get_file_content(self, path: str) -> bytes:
        """
        Read the contents of a file.
        :param path: path to the file to read
        :returns: contents of the file
        """
        return self.sandbox_fs.get_file_content(path)

    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def cat(self, path: str) -> bytes:
        """
        Read the contents of a file.
        :param path: path to the file to read
        :returns: contents of the file as bytes
        """
        return self.sandbox_fs.cat(path)

    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def mkdir(self, path: str, create_recursive: bool = True):
        """
        Create a directory.
        :param path: path to the directory to create
        :param create_recursive: if True, create parent directories if they do not exist
        :returns: None
        """
        # Map create_recursive to create_parents for compatibility
        return self.sandbox_fs.mkdir(path, create_parents=create_recursive)

    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def mv(self, path1: str, path2: str):
        """
        Move a file or directory.
        :param path1: path to the file or directory to move
        :param path2: path to the destination
        :returns: None
        """
        return self.sandbox_fs.mv(path1, path2)

    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def ls(self, path: str = ".", detail: bool = False):
        """
        List the contents of a directory.
        :param path: path to list, defaults to '.'
        :param detail: if True, return detailed information about each file
        :returns: list of files and directories in the directory
        """
        return self.sandbox_fs.ls(path, detail=detail)

    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def rm(self, path: str, recursive: bool = False):
        """
        Remove a file or directory.
        :param path: path to the file or directory to remove
        :param recursive: if True, remove the directory and all its contents
        :returns: None
        """
        return self.sandbox_fs.rm(path, recursive=recursive)

    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def rmdir(self, path: str):
        """
        Remove a directory.
        :param path: path to the directory to remove
        :returns: None
        """
        return self.sandbox_fs.rmdir(path)

    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def exists(self, path: str):
        """
        Check if a file or directory exists.
        :param path: path to the file or directory to check
        :returns: True if the file or directory exists, False otherwise
        """
        return self.sandbox_fs.exists(path)

    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def info(self, path: str, **kwargs: dict[str, Any]):
        """
        Get information about a file or directory.
        :param path: path to the file or directory to get information about
        :param kwargs: additional arguments to pass to the file system
        :returns: information about the file or directory
        """
        return self.sandbox_fs.info(path, **kwargs)

    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def tree(self, path: str = ".") -> str:
        """
        Generate a string representing the directory and file structure in a tree format.
        :param path: Path to start the tree view from, defaults to the root of the sandbox
        :returns: A string representing the directory tree
        """
        return self.sandbox_fs.tree(path)

    def load_file_system_from_path(self, path: str):
        """
        Load file system from a path.
        :param path: path to load the file system from
        """
        return self.sandbox_fs.load_file_system_from_path(path)

    def get_state(self) -> dict[str, Any]:
        """
        Get the current state of the file system in the original VirtualFileSystem format.
        This maintains backward compatibility with previously stored states.
        :returns: dictionary representing the current state
        """
        return self.sandbox_fs.get_state()

    def load_state(self, state_dict: dict[str, Any]):
        self.sandbox_fs.load_state(state_dict)

    @property
    def tmpdir(self) -> str:
        """
        Get the temporary directory path used by the sandbox file system. For backward compatibility with the SandboxLocalFileSystem API.
        :returns: path to the temporary directory
        """
        return self.sandbox_fs.tmpdir

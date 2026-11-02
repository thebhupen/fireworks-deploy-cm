# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import os

import fsspec
import pytest

from are.simulation.apps.sandbox_file_system import SandboxLocalFileSystem

FILES = {
    "/source_dir/test1.txt": "test with emojis 💵",
    "/source_dir/test2.txt": "test with emojis 💵💵",
    "/source_dir/images/llama.jpg": b"I am a binary image !",
    "/source_dir/images/cat.png": b"I am a cat image!",
    "/source_dir/documents/readme.md": "# Documentation\nThis is a test markdown file.",
    "/source_dir/documents/reports/q1_report.txt": "Q1 Financial Report\n\nRevenue: $1,000,000\nExpenses: $750,000",
    "/download_dir/models/model_weights.bin": b"Binary model weights content",
    "/download_dir/datasets/eval_dataset.csv": "Evaluation dataset content",
}


def dummy_fs_population(fs: SandboxLocalFileSystem):
    """Populate the filesystem with a test directory structure."""

    # Create all files
    for path, content in FILES.items():
        try:
            fs.mkdir(os.path.dirname(path), create_parents=True, exist_ok=True)
        except FileExistsError:
            pass
        if isinstance(content, bytes):
            fs.write_bytes(path, content)
        else:
            with fs.open(path, "w") as file:
                file.write(content)


@pytest.fixture
def fs():
    fs = SandboxLocalFileSystem()
    dummy_fs_population(fs)
    yield fs
    del fs


@pytest.fixture
def fs_fromstate():
    fs = SandboxLocalFileSystem()

    # Create a simple file structure that matches part of the demo_filesystem
    state_dict = {
        "files": {
            "name": "",
            "type": "directory",
            "children": [
                {
                    "name": "Documents",
                    "type": "directory",
                    "children": [
                        {"name": "weatherHistory.csv", "type": "file"},
                    ],
                },
                {
                    "name": "Downloads",
                    "type": "directory",
                    "children": [
                        {"name": "2407.21783v2.pdf", "type": "file"},
                    ],
                },
                {
                    "name": "Pictures",
                    "type": "directory",
                    "children": [
                        {
                            "name": "Personal",
                            "type": "directory",
                            "children": [
                                {
                                    "name": "Nature",
                                    "type": "directory",
                                    "children": [
                                        {
                                            "name": "Alpine_Lake_2022.jpg",
                                            "type": "file",
                                        }
                                    ],
                                },
                            ],
                        }
                    ],
                },
            ],
        }
    }

    # Load the state
    fs.load_state(state_dict)
    return fs


def test_file_system_not_cached():
    fs = SandboxLocalFileSystem()
    fs2 = SandboxLocalFileSystem()

    assert fs is not fs2
    assert fs.tmpdir != fs2.tmpdir


def test_sandbox_path_handling(fs: SandboxLocalFileSystem):
    """Test that the sandbox file system correctly handles paths and hides the temporary directory."""
    # Test ls with root path
    root_results = fs.ls("/")
    root_names = set(root_results)
    expected_root_names = {"/source_dir", "/download_dir"}
    assert root_names == expected_root_names, (
        f"Expected {expected_root_names}, got {root_names}"
    )

    # Test ls with absolute path
    source_dir_results = fs.ls("/source_dir")
    source_dir_names = set(source_dir_results)
    expected_source_dir_names = {
        "/source_dir/test1.txt",
        "/source_dir/test2.txt",
        "/source_dir/images",
        "/source_dir/documents",
    }
    assert source_dir_names == expected_source_dir_names

    # Test ls with relative path
    rel_source_dir_results = fs.ls("source_dir")
    rel_source_dir_names = set(rel_source_dir_results)
    assert rel_source_dir_names == expected_source_dir_names


def test_get_state(fs: SandboxLocalFileSystem):
    """Test that the get_state method correctly returns the file system structure."""
    # Get the state
    state = fs.get_state()

    # Verify the state structure
    assert "files" in state
    assert "tmpdir" in state
    assert state["tmpdir"] == fs.tmpdir

    expected_files = {
        os.path.join(path, f)  # type: ignore
        for (path, _d, files) in fs.walk("/", detail=False)
        for f in files
    }

    def extract_files(path, state):
        if state["type"] == "file":
            return [os.path.join(path, state["name"])]
        elif state["type"] == "directory":
            files = []
            for child in state.get("children", []):
                files.extend(extract_files(os.path.join(path, state["name"]), child))
            return files
        return []

    actual_files = set(extract_files("/", state["files"]))

    assert actual_files == expected_files


def test_load_state(fs: SandboxLocalFileSystem):
    """Test that the load_state method correctly restores the file system structure."""
    # Get the state of the original filesystem
    original_state = fs.get_state()

    # Create a new filesystem
    new_fs = SandboxLocalFileSystem()

    # Load the state into the new filesystem
    new_fs.load_state(original_state)

    # Get the set of files in the original filesystem
    original_files = set()
    for path, _, files in fs.walk("/", detail=False):
        for file in files:
            original_files.add(os.path.join(path or "/", file))  # type: ignore

    # Get the set of files in the new filesystem
    new_files = set()
    for path, _, files in new_fs.walk("/", detail=False):
        for file in files:
            new_files.add(os.path.join(path or "/", file))  # type: ignore

    # Compare the sets of files
    assert original_files == new_files

    # Clean up
    del new_fs


def test_tree(fs: SandboxLocalFileSystem):
    """Test that the tree method correctly generates a string representation of the directory structure."""
    # Get the tree representation of the root directory
    tree_str = fs.tree("/")

    # Define the expected tree structure for the root directory
    # Note: The exact structure might vary depending on the sorting algorithm used in the tree method
    expected_root_tree = """/
├── download_dir
    ├── datasets
        └── eval_dataset.csv
    └── models
        └── model_weights.bin
└── source_dir
    ├── documents
        ├── readme.md
        └── reports
            └── q1_report.txt
    ├── images
        ├── cat.png
        └── llama.jpg
    ├── test1.txt
    └── test2.txt
"""
    # Compare the actual tree string with the expected one
    # We strip both strings to handle any potential trailing newline differences
    assert tree_str.strip() == expected_root_tree.strip()

    # Test tree with a specific subdirectory
    subtree_str = fs.tree("/source_dir/documents")

    # Define the expected tree structure for the documents subdirectory
    expected_documents_tree = """documents
├── readme.md
└── reports
    └── q1_report.txt
"""

    # Compare the actual subtree string with the expected one
    assert subtree_str.strip() == expected_documents_tree.strip()


def test_info(fs: SandboxLocalFileSystem):
    """Test that the info method correctly returns information about files and directories."""
    # Test info on a file
    file_info = fs.info("/source_dir/test1.txt")

    # Verify the file info contains the expected keys and values
    assert file_info["name"] == "/source_dir/test1.txt"
    assert file_info["type"] == "file"
    assert file_info["size"] > 0  # File should have some content
    assert "created" in file_info
    assert "mode" in file_info

    # Test info on a directory
    dir_info = fs.info("/source_dir/documents")

    # Verify the directory info contains the expected keys and values
    assert dir_info["name"] == "/source_dir/documents"
    assert dir_info["type"] == "directory"
    assert "created" in dir_info
    assert "mode" in dir_info

    # Test that the real path (tmpdir) is hidden in the result
    assert fs.tmpdir not in file_info["name"]
    assert fs.tmpdir not in dir_info["name"]

    # Test info on a nested file
    nested_file_info = fs.info("/source_dir/documents/reports/q1_report.txt")
    assert nested_file_info["name"] == "/source_dir/documents/reports/q1_report.txt"
    assert nested_file_info["type"] == "file"

    # Test info on the root directory
    root_info = fs.info("/")
    assert root_info["name"] == "/"
    assert root_info["type"] == "directory"


def test_cat(fs: SandboxLocalFileSystem):
    """Test that the cat method correctly reads file contents."""
    # Test reading a text file
    content = fs.cat("/source_dir/test1.txt")
    assert content.decode("utf-8") == FILES["/source_dir/test1.txt"]

    # Test reading a binary file
    binary_content = fs.cat("/source_dir/images/llama.jpg")
    assert binary_content == FILES["/source_dir/images/llama.jpg"]

    # Test reading a nested file
    nested_content = fs.cat("/source_dir/documents/reports/q1_report.txt")
    assert (
        nested_content.decode("utf-8")
        == FILES["/source_dir/documents/reports/q1_report.txt"]
    )


def test_makedirs(fs: SandboxLocalFileSystem):
    """Test that the makedirs method correctly creates directories."""
    # Create a new directory structure
    fs.makedirs("/new_dir/subdir/nested", exist_ok=False)

    # Verify the directories were created
    assert fs.exists("/new_dir")
    assert fs.exists("/new_dir/subdir")
    assert fs.exists("/new_dir/subdir/nested")

    # Test exist_ok parameter
    fs.makedirs("/new_dir/subdir/nested", exist_ok=True)  # Should not raise an error

    # Test that makedirs raises an error when exist_ok is False and directory exists
    with pytest.raises(FileExistsError):
        fs.makedirs("/new_dir/subdir/nested", exist_ok=False)


def test_mv(fs: SandboxLocalFileSystem):
    """Test that the mv method correctly moves files and directories."""
    # Move a file
    fs.mv("/source_dir/test1.txt", "/source_dir/test1_moved.txt")

    # Verify the file was moved
    assert not fs.exists("/source_dir/test1.txt")
    assert fs.exists("/source_dir/test1_moved.txt")
    assert (
        fs.cat("/source_dir/test1_moved.txt").decode("utf-8")
        == FILES["/source_dir/test1.txt"]
    )

    # Move a directory
    fs.mv("/source_dir/images", "/images_moved")

    # Verify the directory and its contents were moved
    assert not fs.exists("/source_dir/images")
    assert fs.exists("/images_moved")
    assert fs.exists("/images_moved/llama.jpg")
    assert fs.exists("/images_moved/cat.png")


def test_rm(fs: SandboxLocalFileSystem):
    """Test that the rm method correctly removes files and directories."""
    # Remove a file
    fs.rm("/source_dir/test2.txt")

    # Verify the file was removed
    assert not fs.exists("/source_dir/test2.txt")

    # Test that rm without recursive=True fails on directories
    with pytest.raises(Exception):
        fs.rm("/source_dir/documents")

    # Remove a directory with recursive=True
    fs.rm("/source_dir/documents", recursive=True)

    # Verify the directory and its contents were removed
    assert not fs.exists("/source_dir/documents")
    assert not fs.exists("/source_dir/documents/readme.md")
    assert not fs.exists("/source_dir/documents/reports/q1_report.txt")


def test_exists(fs: SandboxLocalFileSystem):
    """Test that the exists method correctly checks if files and directories exist."""
    # Test existing files and directories
    assert fs.exists("/source_dir")
    assert fs.exists("/source_dir/test1.txt")
    assert fs.exists("/source_dir/documents/readme.md")

    # Test non-existing files and directories
    assert not fs.exists("/nonexistent_dir")
    assert not fs.exists("/source_dir/nonexistent_file.txt")

    # Create a new file and verify it exists
    with fs.open("/new_file.txt", "w") as f:
        f.write("New file content")
    assert fs.exists("/new_file.txt")

    # Remove the file and verify it no longer exists
    fs.rm("/new_file.txt")
    assert not fs.exists("/new_file.txt")


def test_display(fs: SandboxLocalFileSystem):
    """Test that the display method correctly checks if files exist."""
    # Test display on existing files
    assert fs.display("/source_dir/test1.txt") is True
    assert fs.display("/source_dir/documents/readme.md") is True

    # Test display on non-existing files
    assert fs.display("/nonexistent_file.txt") is False

    # Test display on directories
    assert fs.display("/source_dir") is True
    assert fs.display("/nonexistent_dir") is False


def test_open(fs: SandboxLocalFileSystem):
    """Test that the open method correctly opens files for reading and writing."""
    # Test opening a file for reading
    with fs.open("/source_dir/test1.txt", "r") as f:
        content = f.read()
        assert content == FILES["/source_dir/test1.txt"]

    expected_str = "New file content from open 🤡"
    # Test opening a file for writing
    with fs.open("/new_open_file.txt", "w") as f:
        f.write(expected_str)

    # Verify the file was created with the correct content
    assert fs.exists("/new_open_file.txt")
    assert fs.cat("/new_open_file.txt").decode("utf-8") == expected_str

    append_str = "\nAppended 🤖 content "
    # Test opening a file for appending
    with fs.open("/new_open_file.txt", "a") as f:
        f.write(append_str)

    # Verify the content was appended
    assert fs.cat("/new_open_file.txt").decode("utf-8") == (expected_str + append_str)

    # Test opening a binary file
    with fs.open("/source_dir/images/llama.jpg", "rb") as f:
        binary_content = f.read()
        assert binary_content == FILES["/source_dir/images/llama.jpg"]


def test_fsspec_memory_fallback():
    """Test that SandboxLocalFileSystem can use a memory filesystem as a fallback source."""
    # Create a memory filesystem
    mem_fs = fsspec.filesystem("memory")

    # Create test files in the memory filesystem
    test_files = {
        "/demo_filesystem/test.txt": "Memory filesystem test content",
        "/demo_filesystem/image.jpg": b"Binary image content from memory",
        "/demo_filesystem/docs/readme.md": "# Memory Filesystem\nThis is a test markdown file.",
    }

    # Populate the memory filesystem
    for path, content in test_files.items():
        # Ensure parent directories exist
        mem_fs.makedirs(os.path.dirname(path), exist_ok=True)

        # Write content to the file
        with mem_fs.open(path, "wb" if isinstance(content, bytes) else "w") as f:
            f.write(content)

    # Create a state dictionary that references the files in the memory filesystem
    state_dict = {
        "files": {
            "name": "",
            "type": "directory",
            "children": [
                {"name": "test.txt", "type": "file"},
                {"name": "image.jpg", "type": "file"},
                {
                    "name": "docs",
                    "type": "directory",
                    "children": [{"name": "readme.md", "type": "file"}],
                },
            ],
        }
    }
    # Create a SandboxLocalFileSystem instance
    fs = SandboxLocalFileSystem(state_directory="memory://demo_filesystem")

    # Load the state
    fs.load_state(state_dict)

    # Check that the files exist as placeholders
    assert fs.exists("/test.txt")
    assert fs.exists("/image.jpg")
    assert fs.exists("/docs/readme.md")

    # Check that the files have the correct size in info (from fallback stats)
    assert fs.info("/test.txt")["size"] == len(test_files["/demo_filesystem/test.txt"])
    assert fs.info("/image.jpg")["size"] == len(
        test_files["/demo_filesystem/image.jpg"]
    )
    assert fs.info("/docs/readme.md")["size"] == len(
        test_files["/demo_filesystem/docs/readme.md"]
    )

    # Access the files to trigger lazy loading
    text_content = fs.cat("/test.txt").decode("utf-8")
    binary_content = fs.cat("/image.jpg")
    markdown_content = fs.cat("/docs/readme.md").decode("utf-8")

    # Verify the content matches
    assert text_content == test_files["/demo_filesystem/test.txt"]
    assert binary_content == test_files["/demo_filesystem/image.jpg"]
    assert markdown_content == test_files["/demo_filesystem/docs/readme.md"]


def test_path_traversal_prevention(fs: SandboxLocalFileSystem):
    """Test that the filesystem prevents path traversal attacks."""
    # Test relative path traversal attempts
    with pytest.raises(FileNotFoundError):
        fs.cat("~/.ssh/id_rsa")

    with pytest.raises(FileNotFoundError):
        fs.cat("~abhu/.ssh/id_rsa")

    with pytest.raises(PermissionError):
        fs.cat("../../../etc/passwd")

    with pytest.raises(PermissionError):
        fs.open("../../.ssh/id_rsa", "r")

    with pytest.raises(PermissionError):
        fs.ls("../../../")

    with pytest.raises(PermissionError):
        fs.info("../../..")

    # Test with absolute paths outside the sandbox
    with pytest.raises(FileNotFoundError):
        fs.cat("/etc/passwd")

    with pytest.raises(FileNotFoundError):
        fs.open("/home/.ssh/id_rsa", "r")

    # Test with paths that explicitly include the tmpdir
    with pytest.raises(FileNotFoundError):
        fs.cat(os.path.join(fs.tmpdir, "../../../etc/passwd"))

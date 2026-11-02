# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import json
import os
import random
import string

from fsspec.core import url_to_fs

from are.simulation.apps.sandbox_file_system import SandboxLocalFileSystem
from are.simulation.config import DEMO_FS_PATH

name2path = {
    "wikipedia": os.path.join(DEMO_FS_PATH, "Documents"),
}


def load_file_from_shared_dir(
    fs: SandboxLocalFileSystem, data_type: str, root: str, n_samples: int
):
    """
    Load a file from the shared directory.

    :param fs: The filesystem to load from.
    :param root: The destination path to load to.
    :param source_sub_path: The sub-path in the shared directory to load from.
    :param n_samples: The number of samples to load.
    """
    if data_type not in name2path:
        raise ValueError(f"Invalid data type: {data_type}")
    source_path = name2path[data_type]
    dest_path = root

    if not fs.exists(dest_path):
        fs.makedirs(dest_path)

    try:
        fs_reader, fs_path = url_to_fs(source_path)

        if fs_reader.exists(fs_path):
            files = [
                os.path.basename(f)
                for f in fs_reader.ls(fs_path)
                if f.endswith(".json")
            ]
            sample_files = random.sample(files, min(n_samples, len(files)))

            for file in sample_files:
                src_file_path = os.path.join(fs_path, file)
                dest_file_path = os.path.join(dest_path, file + ".txt")
                with fs.open(dest_file_path, "w") as f:
                    with fs_reader.open(src_file_path, "r") as src_f:
                        raw = json.loads(src_f.read())
                        f.write(raw["text_content"])
        else:
            print(f"Warning: Source path {source_path} does not exist")
    except Exception as e:
        print(f"Warning: Could not load files from {source_path}: {e}")


def default_fs_folders(fs: SandboxLocalFileSystem) -> None:
    """
    Populate the filesystem with default folders.

    :param fs: The filesystem to populate.
    """
    dirs = [
        "Applications",
        "Desktop",
        "Documents",
        "Downloads",
        "Music",
        "Pictures",
        "Public",
        "Templates",
        "Videos",
    ]
    for dir in dirs:
        if fs.exists(dir):
            print(f"Directory {dir} already exists.")
            continue
        fs.mkdir(dir)


def random_fs_population(
    fs: SandboxLocalFileSystem,
    available_files: dict = {},
    path: str = "",
    seed=0,
    depth=3,
    max_files=5,
    max_folders=2,
) -> None:
    """
    Randomly populate the filesystem with folders and files using available files.

    :param fs: The filesystem to populate.
    :param available_files: Dictionary of available files to use.
    :param path: The root path to populate.
    :param seed: Seed for random number generation.
    :param depth: Maximum depth of folder creation.
    :param max_files: Maximum number of files per folder.
    :param max_folders: Maximum number of subfolders per folder.
    """
    random.seed(seed)

    def read_file_content(file_path: str) -> str:
        """Read file content using fsspec."""
        try:
            fs_reader, _ = url_to_fs(file_path)
            with fs_reader.open(file_path, "r") as f:
                raw = json.loads(f.read())
                return raw["text_content"]
        except Exception as e:
            print(f"Warning: Could not read file {file_path}: {e}")
            return "Sample text content"

    def create_random_files_and_folders(path="", current_depth=0):
        if current_depth > depth:
            return
        # Create random files from available files
        file_keys = list(available_files.keys())
        if not file_keys:
            raise ValueError("No files available for population")

        for _ in range(random.randint(1, min(max_files, len(file_keys)))):
            file_key = random.choice(file_keys)
            file_info = available_files[file_key]
            file_path = os.path.join(path, file_info["file_name"])
            with fs.open(file_path, "w") as f:
                # Read file content using the appropriate method
                content = read_file_content(file_info["full_path"])
                f.write(content)
            if len(file_keys) > 1:
                file_keys.remove(file_key)  # Optionally remove to avoid reuse
        # Create random subfolders
        for _ in range(random.randint(1, max_folders)):
            folder_name = "".join(random.choices(string.ascii_letters, k=10))
            folder_path = os.path.join(path, folder_name)
            if fs.exists(folder_path):
                print(f"Directory {folder_path} already exists.")
            else:
                fs.mkdir(folder_path)
            create_random_files_and_folders(folder_path, current_depth + 1)

    # Start the recursive population
    create_random_files_and_folders(path=path)


def set_available_files(path: str | None = None):
    available_files = {}

    if path is None:
        path = os.path.join(DEMO_FS_PATH, "Documents")

    try:
        fs, fs_path = url_to_fs(path)

        if fs.exists(fs_path):
            # Try to scan subdirectories first (for structured datasets)
            try:
                for item_info in fs.ls(fs_path, detail=True):
                    if item_info.get("type") == "directory":
                        # Scan subdirectory for files
                        sub_folder_path = item_info["name"]
                        for file_info in fs.ls(sub_folder_path, detail=True):
                            if file_info.get("type") == "file":
                                file_name = os.path.basename(file_info["name"])
                                available_files[file_name] = {
                                    "file_name": file_name,
                                    "full_path": file_info["name"],
                                    "meta": {},
                                }
                    elif item_info.get("type") == "file":
                        # Direct file in the path
                        file_name = os.path.basename(item_info["name"])
                        if file_name.endswith(".json"):
                            available_files[file_name] = {
                                "file_name": file_name,
                                "full_path": item_info["name"],
                                "meta": {},
                            }
            except Exception:
                # Fallback: scan for files directly in the path
                for file_info in fs.ls(fs_path, detail=True):
                    if file_info.get("type") == "file":
                        file_name = os.path.basename(file_info["name"])
                        if file_name.endswith(".json"):
                            available_files[file_name] = {
                                "file_name": file_name,
                                "full_path": file_info["name"],
                                "meta": {},
                            }
    except Exception as e:
        print(f"Warning: Could not access filesystem at {path}: {e}")
        available_files = {}

    return available_files

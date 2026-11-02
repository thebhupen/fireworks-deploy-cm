# ScenarioFindImageFile

## Overview

The `scenario_find_image_file` is a basic exploration scenario that tests an agent's capability to access the file system and locate a specific file. The task requires the agent to find an image file (`llama.jpg`) in the current directory among multiple other files.

This scenario creates a sandbox environment with:
- 10 randomly named text files (`.txt` extension) with UUID-based names
- 1 binary image file named `llama.jpg`

The agent receives a user request to "find the image file in the current directory" and must identify and return the correct filename (`llama.jpg`).

# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


"""Benchmark module for running and evaluating scenarios.

This package provides tools for running benchmark scenarios from local files or
HuggingFace datasets. It supports various modes including standard execution,
oracle mode, and offline validation.

Main components:
- cli: Command-line interface for running benchmarks
- utils: Core utilities for scenario processing and execution
- local_loader: Functions for loading scenarios from local files
- huggingface_loader: Functions for loading scenarios from HuggingFace datasets
"""

from are.simulation.benchmark.cli import main
from are.simulation.benchmark.scenario_executor import run_dataset

__all__ = ["main", "run_dataset"]

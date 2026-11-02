# Meta Platforms, Inc. and affiliates. Confidential and proprietary.

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("meta-agents-research-environments")
except PackageNotFoundError:
    # package is not installed
    __version__ = "unknown"

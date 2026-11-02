# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


"""
This file is maintained for backward compatibility.
The functionality has been moved to the benchmark package.
Please import from are.simulation.benchmark directly in new code.
"""

if __name__ == "__main__":
    from are.simulation.benchmark.cli import main

    main()

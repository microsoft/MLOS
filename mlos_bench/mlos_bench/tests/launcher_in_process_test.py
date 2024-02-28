#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests to check the launcher and the main optimization loop in-process.
"""

from typing import List

import pytest

from mlos_bench.run import _main


@pytest.mark.parametrize(
    ("argv", "expected_score"), [
        ([
            "--config", "mlos_bench/mlos_bench/tests/config/cli/mock-bench.jsonc",
        ], 65.6742),
        ([
            "--config", "mlos_bench/mlos_bench/tests/config/cli/mock-opt.jsonc",
            "--trial_config_repeat_count", "3",
            "--max_iterations", "3",
        ], 64.2758),
    ]
)
def test_main_bench(argv: List[str], expected_score: float) -> None:
    """
    Run mlos_bench optimization loop with given config and check the results.
    """
    (score, _config) = _main(argv)
    assert pytest.approx(score, 1e-6) == expected_score

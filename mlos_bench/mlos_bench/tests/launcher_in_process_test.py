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
    ("argv", "expected_score"),
    [
        (
            [
                "--config",
                "mlos_bench/mlos_bench/tests/config/cli/mock-bench.jsonc",
            ],
            65.6742,
        ),
        (
            [
                "--config",
                "mlos_bench/mlos_bench/tests/config/cli/mock-opt.jsonc",
                "--trial_config_repeat_count",
                "3",
                "--max_suggestions",
                "3",
            ],
            64.53897,
        ),
    ],
)
def test_main_bench(argv: List[str], expected_score: float) -> None:
    """
    Run mlos_bench optimization loop with given config and check the results.
    """
    (score, _config) = _main(argv)
    assert score is not None
    assert pytest.approx(score["score"], 1e-5) == expected_score

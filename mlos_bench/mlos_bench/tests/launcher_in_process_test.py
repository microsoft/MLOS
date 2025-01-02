#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests to check the launcher and the main optimization loop in-process."""


import pytest

from mlos_bench.run import _main


@pytest.mark.parametrize(
    ("argv", "expected_score"),
    [
        (
            [
                "--config",
                "mlos_bench/mlos_bench/tests/config/cli/mock-bench.jsonc",
                "--trial_config_repeat_count",
                "5",
                "--mock_env_seed",
                "-1",  # Deterministic Mock Environment.
            ],
            67.40329,
        ),
        (
            [
                "--config",
                "mlos_bench/mlos_bench/tests/config/cli/mock-opt.jsonc",
                "--trial_config_repeat_count",
                "3",
                "--max-suggestions",
                "3",
                "--mock_env_seed",
                "42",  # Noisy Mock Environment.
            ],
            64.53897,
        ),
        (
            [
                "--config",
                "mlos_bench/mlos_bench/tests/config/cli/test-cli-local-env-bench.jsonc",
                "--globals",
                "experiment_test_local.jsonc",
                "--tunable_values",
                "tunable-values/tunable-values-local.jsonc",
            ],
            123.4,
        ),
        (
            [
                "--config",
                "mlos_bench/mlos_bench/tests/config/cli/test-cli-local-env-opt.jsonc",
                "--globals",
                "experiment_test_local.jsonc",
                "--max-suggestions",
                "3",
            ],
            123.4,
        ),
    ],
)
@pytest.mark.filterwarnings(
    "ignore:.*(Configuration.*was already registered).*:UserWarning:.*flaml_optimizer.*:0"
)
def test_main_bench(argv: list[str], expected_score: float) -> None:
    """Run mlos_bench optimization loop with given config and check the results."""
    (score, _config) = _main(argv)
    assert score is not None
    assert pytest.approx(score["score"], 1e-5) == expected_score

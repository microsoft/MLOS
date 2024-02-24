#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests to check the launcher and the main optimization loop in-process.
"""

from typing import List

import pytest

from mlos_bench.launcher import Launcher
from mlos_bench.run import _optimization_loop


@pytest.mark.parametrize(
    ("argv", "expected_score"), [
        ([
            "--config", "mlos_bench/mlos_bench/tests/config/cli/mock-bench.jsonc",
        ], 65.6742),
        ([
            "--config", "mlos_bench/mlos_bench/tests/config/cli/mock-opt.jsonc",
            "--trial_config_repeat_count", "3",
            "--max_iterations", "3",
        ], 64.8847),
    ]
)
def test_main_bench(argv: List[str], expected_score: float) -> None:
    """
    Run mlos_bench optimization loop with given config and check the results.
    """
    launcher = Launcher("mlos_bench", "TEST RUN", argv=argv)
    (score, _config) = _optimization_loop(
        env=launcher.environment,
        opt=launcher.optimizer,
        storage=launcher.storage,
        root_env_config=launcher.root_env_config,
        global_config=launcher.global_config,
        do_teardown=launcher.teardown,
        trial_config_repeat_count=launcher.trial_config_repeat_count,
    )
    assert pytest.approx(score, 1e-6) == expected_score

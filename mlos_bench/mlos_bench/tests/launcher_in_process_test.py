#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests to check the launcher and the main optimization loop in-process.
"""

import pytest

from mlos_bench.launcher import Launcher
from mlos_bench.run import _optimization_loop


def test_main_bench() -> None:
    """
    Run mlos_bench optimization loop with given config and check the results.
    """
    launcher = Launcher("mlos_bench", "TEST RUN", argv=[
        "--config",
        "mlos_bench/mlos_bench/tests/config/cli/mock-bench.jsonc",
    ])
    (score, _config) = _optimization_loop(
        env=launcher.environment,
        opt=launcher.optimizer,
        storage=launcher.storage,
        root_env_config=launcher.root_env_config,
        global_config=launcher.global_config,
        do_teardown=launcher.teardown,
        trial_config_repeat_count=launcher.trial_config_repeat_count,
    )
    assert pytest.approx(score, 1e-6) == 65.6742

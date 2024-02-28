#!/usr/bin/env python3
#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
OS Autotune main optimization loop.

Note: this script is also available as a CLI tool via pip under the name "mlos_bench".

See `--help` output for details.
"""

import logging
from typing import List, Optional, Tuple

from mlos_bench.launcher import Launcher
from mlos_bench.tunables.tunable_groups import TunableGroups
from mlos_bench.schedulers.sync_scheduler import SyncScheduler

_LOG = logging.getLogger(__name__)


def _main(argv: Optional[List[str]] = None) -> Tuple[Optional[float], Optional[TunableGroups]]:

    launcher = Launcher("mlos_bench", "Systems autotuning and benchmarking tool", argv=argv)

    # TODO: Instantiate Scheduler from JSON config
    scheduler = SyncScheduler(
        config={
            "experiment_id": "UNDEFINED - override from global config",
            "trial_id": 0,    # Override from global config
            "config_id": -1,  # Override from global config
            "trial_config_repeat_count": launcher.trial_config_repeat_count,
            "teardown": launcher.teardown,
        },
        global_config=launcher.global_config,
        environment=launcher.environment,
        optimizer=launcher.optimizer,
        storage=launcher.storage,
        root_env_config=launcher.root_env_config,
    )

    with scheduler.context() as scheduler_context:
        scheduler_context.start()

    (score, _config) = result = scheduler.get_best_observation()
    # NOTE: This log line is used in test_launch_main_app_* unit tests:
    _LOG.info("Final score: %s", score)
    return result


if __name__ == "__main__":
    _main()

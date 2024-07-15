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
from typing import Dict, List, Optional, Tuple

from mlos_bench.launcher import Launcher
from mlos_bench.tunables.tunable_groups import TunableGroups

_LOG = logging.getLogger(__name__)


def _main(
    argv: Optional[List[str]] = None,
) -> Tuple[Optional[Dict[str, float]], Optional[TunableGroups]]:

    launcher = Launcher("mlos_bench", "Systems autotuning and benchmarking tool", argv=argv)

    with launcher.scheduler as scheduler_context:
        scheduler_context.start()
        scheduler_context.teardown()

    (score, _config) = result = launcher.scheduler.get_best_observation()
    # NOTE: This log line is used in test_launch_main_app_* unit tests:
    _LOG.info("Final score: %s", score)
    return result


if __name__ == "__main__":
    _main()

#!/usr/bin/env python3
#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
mlos_bench main optimization loop and benchmark runner CLI.

Note: this script is also available as a CLI tool via ``pip`` under the name ``mlos_bench``.

See the current ``--help`` `output for details <../../../mlos_bench.run.usage.html>`_.

See Also
--------
mlos_bench.config : documentation on the configuration system.
mlos_bench.launcher.Launcher : class is responsible for processing the CLI args.
"""

import logging
import sys

import numpy as np

from mlos_bench.launcher import Launcher
from mlos_bench.tunables.tunable_groups import TunableGroups

_LOG = logging.getLogger(__name__)


def _sanity_check_results(launcher: Launcher) -> None:
    """Do some sanity checking on the results and throw an exception if it looks like
    something went wrong.
    """
    basic_err_msg = "Check configuration, scripts, and logs for details."

    # Check if the scheduler has any trials.
    if not launcher.scheduler.trial_count:
        raise RuntimeError(f"No trials were run. {basic_err_msg}")

    # Check if the scheduler ran the expected number of trials.
    expected_trial_count = min(
        launcher.scheduler.max_trials if launcher.scheduler.max_trials > 0 else np.inf,
        launcher.scheduler.trial_config_repeat_count * launcher.optimizer.max_suggestions,
    )
    if launcher.scheduler.trial_count < expected_trial_count:
        raise RuntimeError(
            f"Expected {expected_trial_count} trials, "
            f"but only {launcher.scheduler.trial_count} were run. {basic_err_msg}"
        )

    # Check to see if "too many" trials seem to have failed (#523).
    unsuccessful_trials = [t for t in launcher.scheduler.ran_trials if not t.status.is_succeeded()]
    if len(unsuccessful_trials) > 0.2 * launcher.scheduler.trial_count:
        raise RuntimeWarning(
            "Too many trials failed: "
            f"{len(unsuccessful_trials)} out of {launcher.scheduler.trial_count}. "
            f"{basic_err_msg}"
        )


def _main(
    argv: list[str] | None = None,
) -> tuple[dict[str, float] | None, TunableGroups | None]:
    launcher = Launcher("mlos_bench", "Systems autotuning and benchmarking tool", argv=argv)

    with launcher.scheduler as scheduler_context:
        scheduler_context.start()
        scheduler_context.teardown()

    _sanity_check_results(launcher)

    (score, _config) = result = launcher.scheduler.get_best_observation()
    # NOTE: This log line is used in test_launch_main_app_* unit tests:
    _LOG.info("Final score: %s", score)
    return result


def _shell_main(
    argv: list[str] | None = None,
) -> int:
    (best_score, best_config) = _main(argv)
    # Exit zero if it looks like the overall operation was successful.
    # TODO: Improve this sanity check to be more robust.
    if (
        best_score
        and best_config
        and all(isinstance(score_value, float) for score_value in best_score.values())
    ):
        return 0
    else:
        raise ValueError(f"Unexpected result: {best_score=}, {best_config=}")


if __name__ == "__main__":
    sys.exit(_shell_main())

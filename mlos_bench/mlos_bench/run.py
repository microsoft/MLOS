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
from typing import Optional, Tuple, Dict, Any

from mlos_bench.launcher import Launcher
from mlos_bench.optimizers.base_optimizer import Optimizer
from mlos_bench.environments.base_environment import Environment
from mlos_bench.storage.base_storage import Storage
from mlos_bench.environments.status import Status
from mlos_bench.tunables.tunable_groups import TunableGroups

_LOG = logging.getLogger(__name__)


def _main() -> None:

    launcher = Launcher("mlos_bench")

    result = _optimize(
        launcher.environment,
        launcher.optimizer,
        launcher.storage,
        launcher.root_env_config,
        launcher.global_config
    )

    _LOG.info("Final result: %s", result)

    if launcher.teardown:
        launcher.environment.teardown()


def _optimize(env: Environment,
              opt: Optimizer,
              storage: Storage,
              root_env_config: str,
              global_config: Dict[str, Any]) -> Tuple[Optional[float], Optional[TunableGroups]]:
    """
    Main optimization loop.

    Parameters
    ----------
    env : Environment
        benchmarking environment to run the optimization on.
    opt : Optimizer
        An interface to mlos_core optimizers.
    storage : Storage
        A storage system to persist the experiment data.
    root_env_config : str
        A path to the root JSON configuration file of the benchmarking environment.
    global_config : dict
        Global configuration parameters.
    """
    experiment_id = global_config["experimentId"].strip()
    trial_id = int(global_config.get("trialId", 1))
    # Start new or resume the existing experiment. Verify that the
    # experiment configuration is compatible with the previous runs.
    # If the `merge` config parameter is present, merge in the data
    # from other experiments and check for compatibility.
    with storage.experiment(experiment_id=experiment_id,
                            trial_id=trial_id,
                            root_env_config=root_env_config,
                            description=env.name,
                            opt_target=opt.target) as exp:

        _LOG.info("Experiment: %s Env: %s Optimizer: %s", exp, env, opt)

        # Load (tunable values, benchmark scores) to warm-up the optimizer.
        # `.load()` returns data from ALL merged-in experiments and attempts
        # to impute the missing tunable values.
        (configs, scores) = exp.load()
        opt.bulk_register(configs, scores)

        # First, complete any pending trials.
        for trial in exp.pending_trials():
            _run(env, opt, trial, global_config)

        # Then, run new trials until the optimizer is done.
        while opt.not_converged():
            tunables = opt.suggest()
            trial = exp.new_trial(tunables)
            _run(env, opt, trial, global_config)

    (best_score, best_config) = opt.get_best_observation()
    _LOG.info("Env: %s best score: %s", env, best_score)
    return (best_score, best_config)


def _run(env: Environment, opt: Optimizer,
         trial: Storage.Trial, global_config: Dict[str, Any]) -> None:
    """
    Run a single trial.

    Parameters
    ----------
    env : Environment
        benchmarking environment to run the optimization on.
    opt : Optimizer
        An interface to mlos_core optimizers.
    storage : Storage
        A storage system to persist the experiment data.
    global_config : dict
        Global configuration parameters.
    """
    _LOG.info("Trial: %s", trial)

    if not env.setup(trial.tunables, trial.config(global_config)):
        _LOG.warning("Setup failed: %s :: %s", env, trial.tunables)
        trial.update(Status.FAILED)
        opt.register(trial.tunables, Status.FAILED)
        return

    # In async mode, poll the environment for status and telemetry
    # and update the storage with the intermediate results.
    (status, telemetry) = env.status()
    trial.update_telemetry(status, telemetry)

    (status, results) = env.run()  # Block and wait for the final result.
    _LOG.info("Results: %s :: %s\n%s", trial.tunables, status, results)
    trial.update(status, results)
    opt.register(trial.tunables, status, results)


if __name__ == "__main__":
    _main()

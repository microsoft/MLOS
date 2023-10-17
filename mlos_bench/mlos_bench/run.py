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

import json
import logging
from datetime import datetime
from typing import Optional, Tuple, Dict, Any

from mlos_bench.launcher import Launcher
from mlos_bench.optimizers.base_optimizer import Optimizer
from mlos_bench.environments.base_environment import Environment
from mlos_bench.storage.base_storage import Storage
from mlos_bench.environments.status import Status
from mlos_bench.tunables.tunable_groups import TunableGroups

_LOG = logging.getLogger(__name__)


def _main() -> None:

    launcher = Launcher("mlos_bench", "Systems autotuning and benchmarking tool")

    result = _optimize(
        env=launcher.environment,
        opt=launcher.optimizer,
        storage=launcher.storage,
        root_env_config=launcher.root_env_config,
        global_config=launcher.global_config,
        do_teardown=launcher.teardown
    )

    _LOG.info("Final result: %s", result)


def _optimize(*,
              env: Environment,
              opt: Optimizer,
              storage: Storage,
              root_env_config: str,
              global_config: Dict[str, Any],
              do_teardown: bool) -> Tuple[Optional[float], Optional[TunableGroups]]:
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
    do_teardown : bool
        If True, teardown the environment at the end of the experiment
    """
    # pylint: disable=too-many-locals
    if _LOG.isEnabledFor(logging.INFO):
        _LOG.info("Root Environment:\n%s", env.pprint())

    experiment_id = global_config["experiment_id"].strip()
    trial_id = int(global_config.get("trial_id", 1))
    config_id = int(global_config.get("config_id", -1))

    # Start new or resume the existing experiment. Verify that the
    # experiment configuration is compatible with the previous runs.
    # If the `merge` config parameter is present, merge in the data
    # from other experiments and check for compatibility.
    with env as env_context, storage.experiment(experiment_id=experiment_id,
                                                trial_id=trial_id,
                                                root_env_config=root_env_config,
                                                description=env.name,
                                                opt_target=opt.target) as exp:

        _LOG.info("Experiment: %s Env: %s Optimizer: %s", exp, env, opt)

        if opt.supports_preload:
            # Load (tunable values, benchmark scores) to warm-up the optimizer.
            # `.load()` returns data from ALL merged-in experiments and attempts
            # to impute the missing tunable values.
            (configs, scores, status) = exp.load()
            opt.bulk_register(configs, scores, status)
            # Complete any pending trials.
            for trial in exp.pending_trials():
                _run(env_context, opt, trial, global_config)
        else:
            _LOG.warning("Skip pending trials and warm-up: %s", opt)

        # Now run new trials until the optimizer is done.
        while opt.not_converged():

            tunables = opt.suggest()

            if config_id > 0:
                tunable_values = exp.load_config(config_id)
                tunables.assign(tunable_values)
                _LOG.info("Load config from storage: %d", config_id)
                if _LOG.isEnabledFor(logging.DEBUG):
                    _LOG.debug("Config %d ::\n%s",
                               config_id, json.dumps(tunable_values, indent=2))
                config_id = -1

            trial = exp.new_trial(tunables, config={
                "optimizer": opt.name,
                "opt_target": opt.target,
                "opt_direction": "min" if opt.is_min else "max",
            })
            _run(env_context, opt, trial, global_config)

        if do_teardown:
            env_context.teardown()

    (best_score, best_config) = opt.get_best_observation()
    _LOG.info("Env: %s best score: %s", env, best_score)
    return (best_score, best_config)


def _run(env_context: Environment, opt: Optimizer,
         trial: Storage.Trial, global_config: Dict[str, Any]) -> None:
    """
    Run a single trial.

    Parameters
    ----------
    env_context : Environment
        Benchmarking environment context to run the optimization on.
    opt : Optimizer
        An interface to mlos_core optimizers.
    storage : Storage
        A storage system to persist the experiment data.
    global_config : dict
        Global configuration parameters.
    """
    _LOG.info("Trial: %s", trial)

    if not env_context.setup(trial.tunables, trial.config(global_config)):
        _LOG.warning("Setup failed: %s :: %s", env_context, trial.tunables)
        # FIXME: Use the actual timestamp from the environment.
        trial.update(Status.FAILED, datetime.utcnow())
        opt.register(trial.tunables, Status.FAILED)
        return

    (status, results) = env_context.run()  # Block and wait for the final result.
    _LOG.info("Results: %s :: %s\n%s", trial.tunables, status, results)

    # In async mode (TODO), poll the environment for status and telemetry
    # and update the storage with the intermediate results.
    (_, telemetry) = env_context.status()
    # Use the status from `.run()` as it is the final status of the experiment.
    # TODO: Use the `.status()` output in async mode.
    trial.update_telemetry(status, telemetry)

    # FIXME: Use the actual timestamp from the benchmark.
    trial.update(status, datetime.utcnow(), results)
    opt.register(trial.tunables, status, results)


if __name__ == "__main__":
    _main()

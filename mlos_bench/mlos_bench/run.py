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


def _main() -> Tuple[Optional[float], Optional[TunableGroups]]:

    launcher = Launcher("mlos_bench", "Systems autotuning and benchmarking tool")

    result = _optimization_loop(
        env=launcher.environment,
        opt=launcher.optimizer,
        storage=launcher.storage,
        root_env_config=launcher.root_env_config,
        global_config=launcher.global_config,
        do_teardown=launcher.teardown,
        trial_config_repeat_count=launcher.trial_config_repeat_count,
    )

    _LOG.info("Final result: %s", result)
    return result


def _optimization_loop(*,
                       env: Environment,
                       opt: Optimizer,
                       storage: Storage,
                       root_env_config: str,
                       global_config: Dict[str, Any],
                       do_teardown: bool,
                       trial_config_repeat_count: int = 1,
                       ) -> Tuple[Optional[float], Optional[TunableGroups]]:
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
    trial_config_repeat_count : int
        How many trials to repeat for the same configuration.
    """
    if _LOG.isEnabledFor(logging.INFO):
        _LOG.info("Root Environment:\n%s", env.pprint())

    # Start new or resume the existing experiment. Verify that the
    # experiment configuration is compatible with the previous runs.
    # If the `merge` config parameter is present, merge in the data
    # from other experiments and check for compatibility.
    with env as env_context, \
         opt as opt_context, \
         storage.experiment(
            experiment_id=global_config["experiment_id"].strip(),
            trial_id=int(global_config["trial_id"]),
            root_env_config=root_env_config,
            description=env.name,
            tunables=env.tunable_params,
            opt_target=opt.target,
            opt_direction=opt.direction,
         ) as exp:

        _LOG.info("Experiment: %s Env: %s Optimizer: %s", exp, env, opt)

        last_trial_id = -1
        if opt_context.supports_preload:
            # Complete trials that are pending or in-progress.
            _run_schedule(exp, env_context, global_config, running=True)
            # Load past trials data into the optimizer
            last_trial_id = _get_optimizer_suggestions(exp, opt_context, is_warm_up=True)
        else:
            _LOG.warning("Skip pending trials and warm-up: %s", opt)

        config_id = int(global_config.get("config_id", -1))
        if config_id > 0:
            tunables = _load_config(exp, env_context, config_id)
            _schedule_trial(exp, opt_context, tunables, trial_config_repeat_count)

        # Now run new trials until the optimizer is done.
        while opt_context.not_converged():
            # TODO: In the future, _scheduler and _optimizer
            # can be run in parallel in two independent loops.
            _run_schedule(exp, env_context, global_config)
            last_trial_id = _get_optimizer_suggestions(exp, opt_context, last_trial_id, trial_config_repeat_count)

        if do_teardown:
            env_context.teardown()

    (best_score, best_config) = opt.get_best_observation()
    _LOG.info("Env: %s best score: %s", env, best_score)
    return (best_score, best_config)


def _load_config(exp: Storage.Experiment, env_context: Environment,
                 config_id: int) -> TunableGroups:
    """
    Load the existing tunable configuration from the storage.
    """
    tunable_values = exp.load_tunable_config(config_id)
    tunables = env_context.tunable_params.assign(tunable_values)
    _LOG.info("Load config from storage: %d", config_id)
    if _LOG.isEnabledFor(logging.DEBUG):
        _LOG.debug("Config %d ::\n%s",
                   config_id, json.dumps(tunable_values, indent=2))
    return tunables


def _run_schedule(exp: Storage.Experiment, env_context: Environment,
                  global_config: Dict[str, Any], running: bool = False) -> None:
    """
    Scheduler part of the loop. Check for pending trials in the queue and run them.
    """
    for trial in exp.pending_trials(datetime.utcnow(), running=running):
        _run_trial(env_context, trial, global_config)


def _get_optimizer_suggestions(exp: Storage.Experiment, opt_context: Optimizer,
                               last_trial_id: int = -1, trial_config_repeat_count: int = 1,
                               is_warm_up: bool = False) -> int:
    """
    Optimizer part of the loop. Load the results of the executed trials
    into the optimizer, suggest new configurations, and add them to the queue.
    Return the last trial ID processed by the optimizer.
    """
    (trial_ids, configs, scores, status) = exp.load(last_trial_id)
    opt_context.bulk_register(configs, scores, status, is_warm_up)

    tunables = opt_context.suggest()
    _schedule_trial(exp, opt_context, tunables, trial_config_repeat_count)

    return max(trial_ids, default=last_trial_id)


def _schedule_trial(exp: Storage.Experiment, opt: Optimizer,
                    tunables: TunableGroups, trial_config_repeat_count: int = 1) -> None:
    """
    Add a configuration to the queue of trials.
    """
    for repeat_i in range(1, trial_config_repeat_count + 1):
        exp.new_trial(tunables, config={
            # Add some additional metadata to track for the trial such as the
            # optimizer config used.
            # Note: these values are unfortunately mutable at the moment.
            # Consider them as hints of what the config was the trial *started*.
            # It is possible that the experiment configs were changed
            # between resuming the experiment (since that is not currently
            # prevented).
            # TODO: Improve for supporting multi-objective
            # (e.g., opt_target_1, opt_target_2, ... and opt_direction_1, opt_direction_2, ...)
            "optimizer": opt.name,
            "opt_target": opt.target,
            "opt_direction": opt.direction,
            "repeat_i": repeat_i,
            "is_defaults": tunables.is_defaults,
        })


def _run_trial(env: Environment, trial: Storage.Trial,
               global_config: Dict[str, Any]) -> Tuple[Status, Optional[Dict[str, float]]]:
    """
    Run a single trial.

    Parameters
    ----------
    env : Environment
        Benchmarking environment context to run the optimization on.
    storage : Storage
        A storage system to persist the experiment data.
    global_config : dict
        Global configuration parameters.

    Returns
    -------
    (trial_status, trial_score) : (Status, Optional[Dict[str, float]])
        Status and results of the trial.
    """
    _LOG.info("Trial: %s", trial)

    if not env.setup(trial.tunables, trial.config(global_config)):
        _LOG.warning("Setup failed: %s :: %s", env, trial.tunables)
        # FIXME: Use the actual timestamp from the environment.
        trial.update(Status.FAILED, datetime.utcnow())
        return (Status.FAILED, None)

    (status, timestamp, results) = env.run()  # Block and wait for the final result.
    _LOG.info("Results: %s :: %s\n%s", trial.tunables, status, results)

    # In async mode (TODO), poll the environment for status and telemetry
    # and update the storage with the intermediate results.
    (_status, _timestamp, telemetry) = env.status()

    # Use the status and timestamp from `.run()` as it is the final status of the experiment.
    # TODO: Use the `.status()` output in async mode.
    trial.update_telemetry(status, timestamp, telemetry)

    trial.update(status, timestamp, results)
    # Filter out non-numeric scores from the optimizer.
    scores = results if not isinstance(results, dict) \
        else {k: float(v) for (k, v) in results.items() if isinstance(v, (int, float))}
    return (status, scores)


if __name__ == "__main__":
    _main()

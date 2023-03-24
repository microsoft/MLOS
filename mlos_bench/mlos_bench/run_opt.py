#!/usr/bin/env python3
#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
OS Autotune main optimization loop.

See `--help` output for details.
"""

import logging

from mlos_bench.launcher import Launcher
from mlos_bench.optimizer import Optimizer
from mlos_bench.environment import Status, Environment
from mlos_bench.storage import Storage

_LOG = logging.getLogger(__name__)


def _main():

    launcher = Launcher("mlos_bench run_opt")

    launcher.parser.add_argument(
        '--optimizer', required=True,
        help='Path to the optimizer configuration file.')

    launcher.parser.add_argument(
        '--storage', required=True,
        help='Path to the storage configuration file.')

    args = launcher.parse_args()

    env = launcher.load_env()

    opt = Optimizer.load(env.tunable_params(),
                         launcher.load_config(args.optimizer),
                         launcher.global_config)

    storage = Storage.load(env.tunable_params(),
                           launcher.load_config(args.storage),
                           launcher.global_config)

    result = _optimize(env, opt, storage, launcher.global_config)
    _LOG.info("Final result: %s", result)

    if args.teardown:
        env.teardown()


def _optimize(env: Environment, opt: Optimizer,
              storage: Storage, global_config: dict):
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
    global_config : dict
        Global configuration parameters.
    """
    # Start new or resume the existing experiment. Verify that the
    # experiment configuration is compatible with the previous runs.
    # If the `merge` config parameter is present, merge in the data
    # from other experiments and check for compatibility.
    with storage.experiment() as exp:

        _LOG.info("Experiment: %s Env: %s Optimizer: %s", exp, env, opt)

        # Load (tunable values, benchmark scores) to warm-up the optimizer.
        # `.load()` returns data from ALL merged-in experiments and attempts
        # to impute the missing tunable values.
        (configs, scores) = exp.load(opt.target)
        opt.bulk_register(configs, scores)

        # First, complete any pending trials.
        for trial in exp.pending():
            _run(env, opt, trial, global_config)

        # Then, run new trials until the optimizer is done.
        while opt.not_converged():
            tunables = opt.suggest()
            trial = exp.trial(tunables)
            _run(env, opt, trial, global_config)

    best = opt.get_best_observation()
    _LOG.info("Env: %s best result: %s", env, best)
    return best


def _run(env: Environment, opt: Optimizer,
         trial: Storage.Trial, global_config: dict):
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

#!/usr/bin/env python3
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

    launcher = Launcher("OS Autotune optimizer")

    launcher.parser.add_argument(
        '--optimizer', required=True,
        help='Path to the optimizer configuration file.')

    launcher.parser.add_argument(
        '--db', required=True,
        help='Path to the database configuration file.')

    launcher.parser.add_argument(
        '--no-teardown', required=False, default=False, action='store_true',
        help='Disable teardown of the environment after the optimization.')

    args = launcher.parse_args()

    global_config = launcher.global_config
    env = launcher.load_env()

    opt = Optimizer.load(
        env.tunable_params(), launcher.load_config(args.optimizer), global_config)

    storage = Storage.load(launcher.load_config(args.db), global_config)

    result = _optimize(env, opt, storage, global_config)
    _LOG.info("Final result: %s", result)

    if not args.no_teardown:
        env.teardown()


def _optimize(env: Environment, opt: Optimizer, storage: Storage, global_config: dict):
    """
    Main optimization loop.
    """
    # Start new or resume the existing experiment. Verify that
    # the experiment configuration is compatible with the previous runs.
    with storage.experiment() as exp:

        _LOG.info("Experiment: %s Env: %s Optimizer: %s", exp, env, opt)

        # Load (tunable values, status, score) to warm-up the optimizer.
        # `.load()` returns data from ALL merged-in experiments and attempts
        # to impute the missing tunable values.
        opt.update(exp.load())

        # First, complete any pending runs.
        for run in exp.pending():
            _trial(env, opt, run, global_config)

        # Then, run new trials until the optimizer is done.
        while opt.not_converged():
            tunables = opt.suggest()
            with exp.run(tunables) as run:
                _trial(env, opt, run, global_config)

    best = opt.get_best_observation()
    _LOG.info("Env: %s best result: %s", env, best)
    return best


def _trial(env: Environment, opt: Optimizer, run: Storage.Run, global_config: dict):
    """
    Run a single trial.
    """
    _LOG.info("Run: %s", run)

    if not env.setup(run.tunables, run.config(global_config)):
        _LOG.warning("Setup failed: %s :: %s", env, run.tunables)
        run.update(Status.FAILED)
        opt.register(run.tunables, Status.FAILED)
        return

    # In async mode, poll the environment for status and telemetry
    # and update the storage with the intermediate results.
    (status, telemetry) = env.status()
    run.update(status, telemetry)

    (status, score) = env.benchmark()  # Block and wait for the final result.
    _LOG.info("Result: %s :: %s\n%s", run.tunables, status, score)
    run.update(status, score)
    opt.register(run.tunables, status, score)


if __name__ == "__main__":
    _main()

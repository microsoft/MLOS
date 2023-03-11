#!/usr/bin/env python3
"""
OS Autotune main optimization loop.

See `--help` output for details.
"""

import logging

import pandas as pd

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

    result = _optimize(env, opt, storage, global_config["experiment_id"])
    _LOG.info("Final result: %s", result)

    if not args.no_teardown:
        env.teardown()


def _get_score(status: Status, value: pd.DataFrame,
               opt_target: str, opt_direction: str = 'min'):
    """
    Extract a scalar benchmark score from the dataframe.
    """
    if not status.is_succeeded:
        return None
    value = value.loc[0, opt_target]
    return value if opt_direction == 'min' else -value


def _optimize(env: Environment, opt: Optimizer, storage: Storage,
              experiment_id: str, run_id: int = 0):
    """
    Main optimization loop.
    """
    _LOG.info("Experiment: %s Env: %s Optimizer: %s", experiment_id, env, opt)

    # TODO: Think how to provide these parameters.
    opt_target = 'score'
    opt_direction = 'min'

    # Start new or resume the existing experiment. Verify that
    # the experiment configuration is compatible with the previous runs.
    with storage.experiment(experiment_id) as exp:

        # Merge in the data from other experiments. Raise an exception
        # if the tunable parameters or configurations are not compatible.
        exp.merge(["experiment1", "experiment2"])

        # Load (tunable values, status, value) to warm-up the optimizer.
        # This call returns data from ALL merged-in experiments and attempts
        # to impute the missing tunable values.
        tunables_data = exp.load(opt_target, opt_direction)
        opt.update(tunables_data)

        run_id = exp.last_run_id or run_id

        while opt.not_converged():

            run_id += 1
            tunables = opt.suggest()
            _LOG.info("%s:%d Suggestion: %s", experiment_id, run_id, tunables)

            with exp.run(tunables, run_id) as run:

                if not env.setup(tunables):  # pass experiment_id and run_id here
                    _LOG.warning("Setup failed: %s :: %s", env, tunables)
                    run.update(Status.FAILED)
                    opt.register(tunables, Status.FAILED)
                    continue

                (status, value) = env.benchmark()  # Block and wait for the final result.
                # `value` is a DataFrame with one row and one or more benchmark results.
                run.update(status, value)

                value = _get_score(status, value, opt_target, opt_direction)
                _LOG.info("Result: %s = %s :: %s", tunables, status, value)

                opt.register(tunables, status, value)

    best = opt.get_best_observation()
    _LOG.info("Env: %s best result: %s", env, best)
    return best


if __name__ == "__main__":
    _main()

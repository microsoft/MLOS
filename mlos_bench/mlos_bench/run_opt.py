#!/usr/bin/env python3
"""
OS Autotune main optimization loop.

See `--help` output for details.
"""

import logging

from mlos_bench.launcher import Launcher
from mlos_bench.optimizer import Optimizer, load_optimizer
from mlos_bench.environment import Status, Environment

_LOG = logging.getLogger(__name__)


def _main():

    launcher = Launcher("OS Autotune optimizer")

    launcher.parser.add_argument(
        '--optimizer', required=True,
        help='Path to the optimizer configuration file.')

    launcher.parser.add_argument(
        '--no-teardown', required=False, default=False, action='store_true',
        help='Disable teardown of the environment after the optimization.')

    args = launcher.parse_args()

    global_config = launcher.global_config
    env = launcher.load_env()

    opt = load_optimizer(
        env.tunable_params(), launcher.load_config(args.optimizer), global_config)

    db = None

    result = _optimize(env, opt, db, global_config["experimentId"])
    _LOG.info("Final result: %s", result)

    if not args.no_teardown:
        env.teardown()


def _optimize(env: Environment, opt: Optimizer, db,
              experiment_id: str, run_id: int = 0):
    """
    Main optimization loop.
    """
    _LOG.info("Experiment: %s Env: %s Optimizer: %s", experiment_id, env, opt)

    # Get records of (tunables, status, score) from the previous runs
    # of the same experiment (or several compatible experiments).
    (last_run_id, tunables_data) = db.restore(experiment_id)
    opt.update(tunables_data)

    run_id = last_run_id or run_id

    # TODO: Restore the telemetry and the optimization target.
    opt_target = 'score'
    opt_direction = 'min'

    while opt.not_converged():

        run_id += 1
        tunables = opt.suggest()
        _LOG.info("%s:%d Suggestion: %s", experiment_id, run_id, tunables)

        with db.experiment(tunables, experiment_id, run_id) as exp:

            if not env.setup(tunables):  # pass experimentName and experimentId here
                _LOG.warning("Setup failed: %s :: %s", env, tunables)
                exp.update(Status.FAILED)
                opt.register(tunables, Status.FAILED)
                continue

            (status, value) = env.benchmark()  # Block and wait for the final result.
            # `value` is a DataFrame with one row and one or more benchmark results.
            exp.update(status, value)

            value = value.loc[0, opt_target] if status.is_succeeded else None

            _LOG.info("Result: %s = %s :: %s", tunables, status, value)
            opt.register(tunables, status, value)

    best = opt.get_best_observation()
    _LOG.info("Env: %s best result: %s", env, best)
    return best


if __name__ == "__main__":
    _main()

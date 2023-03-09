#!/usr/bin/env python3
"""
OS Autotune main optimization loop.

See `--help` output for details.
"""

import logging

from mlos_bench.launcher import Launcher
from mlos_bench.optimizer import Optimizer
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
    env = launcher.load_env()

    opt = Optimizer.load(
        env.tunable_params(), launcher.load_config(args.optimizer), launcher.global_config)

    result = _optimize(env, opt, args.no_teardown)
    _LOG.info("Final result: %s", result)


def _optimize(env: Environment, opt: Optimizer, no_teardown: bool):
    """
    Main optimization loop.
    """
    _LOG.info("Env: %s Optimizer: %s", env, opt)

    while opt.not_converged():

        tunables = opt.suggest()
        _LOG.info("Suggestion: %s", tunables)

        if not env.setup(tunables):
            _LOG.warning("Setup failed: %s :: %s", env, tunables)
            opt.register(tunables, Status.FAILED)
            continue

        (status, value) = env.benchmark()  # Block and wait for the final result
        value = value.loc[0, 'score'] if status.is_succeeded else None

        _LOG.info("Result: %s = %s :: %s", tunables, status, value)
        opt.register(tunables, status, value)

    if not no_teardown:
        env.teardown()

    best = opt.get_best_observation()
    _LOG.info("Env: %s best result: %s", env, best)
    return best


if __name__ == "__main__":
    _main()

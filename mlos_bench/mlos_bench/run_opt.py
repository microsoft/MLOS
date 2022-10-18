#!/usr/bin/env python3
"""
OS Autotune main optimization loop.

See `--help` output for details.
"""

import logging

from mlos_bench.opt import Optimizer
from mlos_bench.launcher import Launcher

_LOG = logging.getLogger(__name__)


def _main():

    launcher = Launcher("OS Autotune optimizer")

    launcher.parser.add_argument(
        '--no-teardown', required=False, default=False, action='store_true',
        help='Disable teardown of the environment after the optimization.')

    args = launcher.parse_args()
    env = launcher.load_env()

    result = optimize(env, args.no_teardown)
    _LOG.info("Final result: %s", result)


def optimize(env, no_teardown):
    """
    Main optimization loop.
    """
    opt = Optimizer(env.tunable_params())
    _LOG.info("Env: %s Optimizer: %s", env, opt)

    while opt.not_converged():

        tunables = opt.suggest()
        _LOG.info("Suggestion: %s", tunables)

        if not env.setup(tunables):
            # TODO: Report Status.FAILED and continue
            _LOG.warning("Environment setup failed: %s", env)
            break

        bench_result = env.benchmark()  # Block and wait for the final result
        _LOG.info("Result: %s = %s", tunables, bench_result)
        opt.register(tunables, bench_result)

    if not no_teardown:
        env.teardown()

    best = opt.get_best_observation()
    _LOG.info("Env: %s best result: %s", env, best)
    return best


if __name__ == "__main__":
    _main()

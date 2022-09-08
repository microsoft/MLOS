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
    launcher.parse_args()
    env = launcher.load_env()
    result = optimize(env)
    _LOG.info("Final result: %s", result)


def optimize(env):
    """
    Main optimization loop.
    """
    opt = Optimizer(env.tunable_params())
    _LOG.info("Env: %s Optimizer: %s", env, opt)

    while opt.not_converged():

        tunable_values = opt.suggest()
        _LOG.info("Suggestion: %s", tunable_values)
        env.submit(tunable_values)

        bench_result = env.result()  # Block and wait for the final result
        _LOG.info("Result: %s = %s", tunable_values, bench_result)
        opt.register(tunable_values, bench_result)

    best = opt.get_best_observation()
    _LOG.info("Env: %s best result: %s", env, best)
    return best


if __name__ == "__main__":
    _main()

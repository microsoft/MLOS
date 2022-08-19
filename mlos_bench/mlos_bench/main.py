#!/usr/bin/env python3

"""
OS Autotune main optimization loop.
"""

import logging
import argparse

from mlos_bench.opt import Optimizer
from mlos_bench.environment.persistence import load_environment


def optimize(env_config_file):
    """
    Main optimization loop.
    """
    env = load_environment(env_config_file)

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

###############################################################


def _main():

    parser = argparse.ArgumentParser(
        description='OS Autotune optimizer')

    parser.add_argument(
        '--config', required=True,
        help='Path to JSON file with the configuration'
             ' of the benchmarking environment')

    args = parser.parse_args()

    result = optimize(args.config)
    _LOG.info("Final result: %s", result)

###############################################################


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(pathname)s:%(lineno)d %(levelname)s %(message)s',
    datefmt='%H:%M:%S'
)

_LOG = logging.getLogger(__name__)

if __name__ == "__main__":
    _main()

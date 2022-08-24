#!/usr/bin/env python3

"""
OS Autotune main optimization loop.
"""

import json
import logging
import argparse

from mlos_bench.opt import Optimizer
from mlos_bench.environment.persistence import load_environment


def optimize(env_config_file, global_config):
    """
    Main optimization loop.
    """
    env = load_environment(env_config_file, global_config)

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


def _try_parse_extra_args(cmdline):
    """
    Helper function to parse global key/value pairs from the command line.
    """
    _LOG.debug("Extra args: %s", cmdline)

    config = {}
    key = None
    for elem in cmdline:
        if elem.startswith("--"):
            if key is not None:
                raise ValueError("Command line argument has no value: " + key)
            key = elem[2:]
            kv_split = key.split("=", 1)
            if len(kv_split) == 2:
                config[kv_split[0].strip()] = kv_split[1]
                key = None
        else:
            if key is None:
                raise ValueError("Command line argument has no key: " + elem)
            config[key.strip()] = elem
            key = None

    if key is not None:
        raise ValueError("Command line argument has no value: " + key)

    _LOG.debug("Parsed config: %s", config)
    return config


def _main():

    parser = argparse.ArgumentParser(
        description='OS Autotune optimizer')

    parser.add_argument(
        '--config', required=True,
        help='Path to JSON file with the configuration'
             ' of the benchmarking environment')

    parser.add_argument(
        '--global', required=False, dest='global_config',
        help='Path to JSON file that contains additional (sensitive)'
             ' parameters of the benchmarking environment')

    (args, args_rest) = parser.parse_known_args()

    global_config = {}
    if args.global_config is not None:
        with open(args.global_config) as fh_json:
            global_config = json.load(fh_json)

    global_config.update(_try_parse_extra_args(args_rest))

    result = optimize(args.config, global_config)
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

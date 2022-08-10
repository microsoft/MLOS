"""
OS Autotune main optimization loop.
"""

import sys
import json
import logging

from mlos_bench.opt import Optimizer
from mlos_bench.environment import Environment


def optimize(config):
    """
    Main optimization loop.
    """
    env = Environment.from_config(config)

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

    with open(sys.argv[1]) as fh_json:
        config = json.load(fh_json)

    if _LOG.isEnabledFor(logging.DEBUG):
        _LOG.debug("Config:\n%s", json.dumps(config, indent=2))

    result = optimize(config)
    _LOG.info("Final result: %s", result)


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(pathname)s:%(lineno)d %(levelname)s %(message)s',
    datefmt='%H:%M:%S'
)

_LOG = logging.getLogger(__name__)

if __name__ == "__main__":
    _main()

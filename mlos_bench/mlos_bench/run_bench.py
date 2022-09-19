#!/usr/bin/env python3
"""
OS Autotune benchmark launcher without involving the optimizer.
Used mostly for development/testing purposes.

See `--help` output for details.
"""

import logging

from mlos_bench.launcher import Launcher

_LOG = logging.getLogger(__name__)


def _main():

    launcher = Launcher("OS Autotune benchmark")

    launcher.parser.add_argument(
        '--tunables', required=True,
        help='Path to JSON file that contains values of the tunable parameters')

    args = launcher.parse_args()

    tunable_values = Launcher.load_config(args.tunables)
    env = launcher.load_env()

    tunables = env.tunable_params()
    for (key, val) in tunable_values.items():
        tunables[key] = val

    _LOG.info("Benchmark: %s with tunables:\n%s", env, tunables)
    env.submit(tunables)

    bench_result = env.result()  # Block and wait for the final result
    _LOG.info("Result: %s", bench_result)

    env.teardown()


if __name__ == "__main__":
    _main()

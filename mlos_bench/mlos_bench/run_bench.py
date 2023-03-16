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

    launcher = Launcher("mlos_bench run_bench")

    launcher.parser.add_argument(
        '--tunables', nargs="+", required=True,
        help='Path to one or more JSON files that contain values of the tunable parameters.')

    args = launcher.parse_args()

    env = launcher.load_env()
    tunables = env.tunable_params()

    for data_file in args.tunables:
        tunables.assign(launcher.load_config(data_file))

    _LOG.info("Benchmark: %s with tunables:\n%s", env, tunables)
    if env.setup(tunables):
        (status, bench_result) = env.run()  # Block and wait for the final result
        _LOG.info("Status: %s, Result: %s", status, bench_result)
    else:
        _LOG.warning("Environment setup failed: %s", env)

    if args.teardown:
        env.teardown()


if __name__ == "__main__":
    _main()

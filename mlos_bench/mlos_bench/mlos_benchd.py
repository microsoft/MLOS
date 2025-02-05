#!/usr/bin/env python3
#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
mlos_bench background execution daemon.

This script is responsible for polling the storage for runnable experiments and
executing them in parallel.

See the current ``--help`` `output for details.
"""
import argparse
import time
from concurrent.futures import ProcessPoolExecutor

from mlos_bench.run import _main as mlos_bench_main
from mlos_bench.storage import from_config


def _main(args: argparse.Namespace) -> None:
    storage = from_config(config=args.storage)
    poll_interval = float(args.poll_interval)
    num_workers = int(args.num_workers)

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        while True:
            exp_id = storage.get_runnable_experiment()
            if exp_id is None:
                print(f"No runnable experiment found. Sleeping for {poll_interval} second(s).")
                time.sleep(poll_interval)
                continue

            exp = storage.experiments[exp_id]
            root_env_config, _, _ = exp.root_env_config

            executor.submit(
                mlos_bench_main,
                [
                    "--storage",
                    args.storage,
                    "--environment",
                    root_env_config,
                    "--experiment_id",
                    exp_id,
                ],
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="mlos_benchd")
    parser.add_argument(
        "--storage",
        required=True,
        help="Path to the storage configuration file.",
    )
    parser.add_argument(
        "--num_workers",
        required=False,
        default=1,
        help="Number of workers to use. Default is 1.",
    )
    parser.add_argument(
        "--poll_interval",
        required=False,
        default=1,
        help="Polling interval in seconds. Default is 1.",
    )
    _main(parser.parse_args())

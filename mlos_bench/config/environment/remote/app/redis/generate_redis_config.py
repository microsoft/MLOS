#!/usr/bin/env python3
#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Helper script to generate Redis config from tunable parameters JSON.

Run: `./generate_redis_config.py ./input-params.json ./output-redis.cfg`
"""

import json
import argparse


def _main(fname_input: str, fname_output: str) -> None:
    with open(fname_input, "rt", encoding="utf-8") as fh_tunables, \
         open(fname_output, "wt", encoding="utf-8", newline="") as fh_config:
        for (key, val) in json.load(fh_tunables).items():
            line = f'{key} {val}'
            fh_config.write(line + "\n")
            print(line)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="generate Redis config from tunable parameters JSON.")
    parser.add_argument("input", help="JSON file with tunable parameters.")
    parser.add_argument("output", help="Output Redis config file.")
    args = parser.parse_args()
    _main(args.input, args.output)

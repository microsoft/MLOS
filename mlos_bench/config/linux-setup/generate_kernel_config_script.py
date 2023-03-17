#!/usr/bin/env python3
#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Helper script to generate a script to update kernel parameters from tunables JSON.

Run: `./generate_kernel_config_script.py ./kernel-params.json ./config-kernel.sh`
"""

import json
import argparse


def _main(fname_input: str, fname_output: str):
    with open(fname_input, "rt", encoding="utf-8") as fh_tunables, \
         open(fname_output, "wt", encoding="utf-8", newline="") as fh_config:
        for (key, val) in json.load(fh_tunables).items():
            line = f'echo "{val}" > /proc/sys/kernel/{key}'
            fh_config.write(line + "\n")
            print(line)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="generate a script to update kernel parameters from tunables JSON.")
    parser.add_argument("input", help="JSON file with tunable parameters.")
    parser.add_argument("output", help="Output shell script to configure Linux kernel.")
    args = parser.parse_args()
    _main(args.input, args.output)

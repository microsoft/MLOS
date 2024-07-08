#!/usr/bin/env python3
#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Helper script to generate a script to update kernel parameters from tunables JSON.

Run:
    ./generate_kernel_config_script.py \
        ./kernel-params.json ./kernel-params-meta.json \
        ./config-kernel.sh
"""

import argparse
import json


def _main(fname_input: str, fname_meta: str, fname_output: str) -> None:

    with open(fname_input, "rt", encoding="utf-8") as fh_tunables:
        tunables_data = json.load(fh_tunables)

    with open(fname_meta, "rt", encoding="utf-8") as fh_meta:
        tunables_meta = json.load(fh_meta)

    with open(fname_output, "wt", encoding="utf-8", newline="") as fh_config:
        for key, val in tunables_data.items():
            meta = tunables_meta.get(key, {})
            name_prefix = meta.get("name_prefix", "")
            line = f'echo "{val}" > {name_prefix}{key}'
            fh_config.write(line + "\n")
            print(line)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="generate a script to update kernel parameters from tunables JSON."
    )

    parser.add_argument("input", help="JSON file with tunable parameters.")
    parser.add_argument("meta", help="JSON file with tunable parameters metadata.")
    parser.add_argument("output", help="Output shell script to configure Linux kernel.")

    args = parser.parse_args()

    _main(args.input, args.meta, args.output)

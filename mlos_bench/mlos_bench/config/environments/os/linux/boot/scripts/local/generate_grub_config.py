#!/usr/bin/env python3
#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Helper script to generate GRUB config from tunable parameters JSON.

Run: `./generate_grub_config.py ./input-boot-params.json ./output-grub.cfg`
"""

import argparse
import json


def _main(fname_input: str, fname_output: str) -> None:
    with open(fname_input, "rt", encoding="utf-8") as fh_tunables, open(
        fname_output, "wt", encoding="utf-8", newline=""
    ) as fh_config:
        for key, val in json.load(fh_tunables).items():
            line = f'GRUB_CMDLINE_LINUX_DEFAULT="${{GRUB_CMDLINE_LINUX_DEFAULT}} {key}={val}"'
            fh_config.write(line + "\n")
            print(line)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate GRUB config from tunable parameters JSON."
    )
    parser.add_argument("input", help="JSON file with tunable parameters.")
    parser.add_argument("output", help="Output shell script to configure GRUB.")
    args = parser.parse_args()
    _main(args.input, args.output)

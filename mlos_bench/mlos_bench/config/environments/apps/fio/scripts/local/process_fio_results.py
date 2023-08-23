#!/usr/bin/env python3
#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Script for post-processing FIO results for mlos_bench.
"""

import argparse
import json

from typing import Any, Iterator, Tuple

import pandas


def _flat_dict(data: Any, path: str) -> Iterator[Tuple[str, Any]]:
    """
    Flatten every dict in the hierarchy and rename the keys with the dict path.
    """
    if isinstance(data, dict):
        for (key, val) in data.items():
            yield from _flat_dict(val, f"{path}.{key}")
    else:
        yield (path, data)


def _main(input_file: str, output_file: str) -> None:
    """
    Convert FIO read data from JSON to wide CSV.
    """
    with open(input_file, mode='r', encoding='utf-8') as fh_input:
        json_data = json.load(fh_input)

    data = dict(_flat_dict(json_data["jobs"][0], "read"))
    wide_df = pandas.DataFrame([list(data.values())], columns=list(data.keys()))

    wide_df.to_csv(output_file, index=False)
    print(f"Converted: {input_file} -> {output_file}")
    # print(df)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Post-process FIO benchmark results.")

    parser.add_argument(
        "input", help="FIO benchmark results in JSON+ format (downloaded from a remote VM).")
    parser.add_argument(
        "output", help="Converted FIO benchmark data (CSV, to be consumed by mlos_bench).")

    args = parser.parse_args()
    _main(args.input, args.output)

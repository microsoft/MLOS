#!/usr/bin/env python3
#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Script for post-processing redis-benchmark results."""

import argparse

import pandas as pd


def _main(input_file: str, output_file: str) -> None:
    """Re-shape Redis benchmark CSV results from wide to long."""
    df_wide = pd.read_csv(input_file)

    # Format the results from wide to long
    # The target is columns of metric and value to act as key-value pairs.
    df_long = (
        df_wide.melt(id_vars=["test"])
        .assign(metric=lambda df: df["test"] + "_" + df["variable"])
        .drop(columns=["test", "variable"])
        .loc[:, ["metric", "value"]]
    )

    # Add a default `score` metric to the end of the dataframe.
    df_long = pd.concat(
        [
            df_long,
            pd.DataFrame({"metric": ["score"], "value": [df_long.value[df_long.index.max()]]}),
        ]
    )

    df_long.to_csv(output_file, index=False)
    print(f"Converted: {input_file} -> {output_file}")
    # print(df_long)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Post-process Redis benchmark results.")
    parser.add_argument(
        "input",
        help="Redis benchmark results (downloaded from a remote VM).",
    )
    parser.add_argument(
        "output",
        help="Converted Redis benchmark data (to be consumed by OS Autotune framework).",
    )
    args = parser.parse_args()
    _main(args.input, args.output)

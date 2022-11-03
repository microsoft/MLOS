#!/usr/bin/env python3

"""
Script for post-processing redis-benchmark results.
"""

import argparse
import logging
import os

import pandas as pd

_LOG = logging.getLogger(__name__)


def run(output_folder: str) -> str:
    """
    Re-shapes redis-benchmark CSV results from wide to long.
    """

    input_file = "results.csv"
    output_file = "metrics.csv"
    output_path = os.path.join(output_folder, output_file)

    # Read in the redis benchmark results
    df_wide = pd.read_csv(os.path.join(output_folder, input_file))

    # Format the results from wide to long
    # The target is columns of metric and value to act as key-value pairs.
    df_long = (
        df_wide
        .melt(id_vars=["test"])
        .assign(metric=lambda df: df["test"] + "_" + df["variable"])
        .drop(columns=["test", "variable"])
        .loc[:, ["metric", "value"]]
    )

    # Write out the processed results to the same folder
    df_long.to_csv(output_path, index=False)

    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Post-process redis benchmark results. Returns the output file path.")
    parser.add_argument(
        "output_folder", type=str,
        help="Folder container benchmark outputs",
    )
    args = parser.parse_args()

    print(run(args.output_folder))

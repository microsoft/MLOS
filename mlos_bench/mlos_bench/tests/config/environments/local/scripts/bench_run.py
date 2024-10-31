#!/usr/bin/env python3
#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Helper script to run the benchmark and store the results and telemetry in CSV files.

Run:
    ./bench_run.py ./output-metrics.csv ./output-telemetry.csv`
"""

import argparse
from datetime import datetime, timedelta

import pandas


def _main(output_metrics: str, output_telemetry: str) -> None:

    df_metrics = pandas.DataFrame(
        [
            {"metric": "total_time", "value": 123.4},
            {"metric": "latency", "value": 0.1},
            {"metric": "throughput", "value": 1234567},
        ]
    )
    df_metrics.to_csv(output_metrics, index=False)

    # Timestamps are const so we can check them in the tests.
    timestamp = datetime(2024, 10, 25, 13, 45)
    ts_delta = timedelta(seconds=30)

    df_telemetry = pandas.DataFrame(
        [
            {"timestamp": timestamp, "metric": "cpu_load", "value": 0.1},
            {"timestamp": timestamp, "metric": "mem_usage", "value": 20.0},
            {"timestamp": timestamp + ts_delta, "metric": "cpu_load", "value": 0.6},
            {"timestamp": timestamp + ts_delta, "metric": "mem_usage", "value": 33.0},
            {"timestamp": timestamp + 2 * ts_delta, "metric": "cpu_load", "value": 0.5},
            {"timestamp": timestamp + 2 * ts_delta, "metric": "mem_usage", "value": 31.0},
        ]
    )
    df_telemetry.to_csv(output_telemetry, index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run the benchmark and save the results in CSV files."
    )
    parser.add_argument("output_metrics", help="CSV file to save the benchmark results to.")
    parser.add_argument("output_telemetry", help="CSV file for telemetry data.")
    args = parser.parse_args()
    _main(args.output_metrics, args.output_telemetry)

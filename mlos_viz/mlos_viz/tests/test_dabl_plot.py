#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for mlos_viz.dabl.plot.
"""

from mlos_bench.storage.base_experiment_data import ExperimentData
from mlos_viz.dabl import plot as dabl_plot


def test_dabl_plot(exp_data: ExperimentData) -> None:
    """Tests plotting via dabl."""
    dabl_plot(exp_data)

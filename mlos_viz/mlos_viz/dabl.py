#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Small wrapper functions for dabl plotting functions via mlos_bench data.
"""

import dabl

from mlos_bench.storage.base_experiment_data import ExperimentData


def plot(exp_data: ExperimentData) -> None:
    """
    Plots the Experiment results data using dabl.

    Parameters
    ----------
    exp_data : ExperimentData
        The ExperimentData (e.g., obtained from the storage layer) to plot.
    """
    for objective in exp_data.objectives:
        objective_column = ExperimentData.RESULT_COLUMN_PREFIX + objective
        dabl.plot(exp_data.results, objective_column)

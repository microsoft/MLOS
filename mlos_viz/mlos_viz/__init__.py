#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
mlos_viz is a framework to help visualizing, explain, and gain insights from results
from the mlos_bench framework for benchmarking and optimization automation.
"""

from enum import Enum

from mlos_bench.storage.base_experiment_data import ExperimentData


class MlosVizMethod(Enum):
    """
    What method to use for visualizing the experiment results.
    """

    AUTO = "auto"
    DABL = "dabl"


def _plot_optimizer_trends(exp_data: ExperimentData) -> None:
    """
    Plots the optimizer trends for the Experiment.

    Intended to be used from a Jupyter notebook.

    Parameters
    ----------
    exp_data: ExperimentData
        The experiment data to plot.
    """

    raise NotImplementedError("TODO")


def plot(exp_data: ExperimentData, method: MlosVizMethod = MlosVizMethod.AUTO) -> None:
    """
    Plots the results of the experiment.

    Intended to be used from a Jupyter notebook.

    Parameters
    ----------
    exp_data: ExperimentData
        The experiment data to plot.
    method: MlosVizMethod
        The method to use for visualizing the experiment results.
    """

    _plot_optimizer_trends(exp_data)

    if method == MlosVizMethod.AUTO:
        method = MlosVizMethod.DABL

    if MlosVizMethod.DABL:
        import mlos_viz.dabl
        mlos_viz.dabl.plot(exp_data)
    else:
        raise NotImplementedError(f"Unhandled method: {method}")

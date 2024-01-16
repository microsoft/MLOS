#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
mlos_viz is a framework to help visualizing, explain, and gain insights from results
from the mlos_bench framework for benchmarking and optimization automation.
"""

from enum import Enum

import warnings

from matplotlib import pyplot as plt
import seaborn as sns

from mlos_bench.storage.base_experiment_data import ExperimentData


class MlosVizMethod(Enum):
    """
    What method to use for visualizing the experiment results.
    """

    AUTO = "dabl"   # use dabl as the current default
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
    for objective in exp_data.objectives:
        objective_column = ExperimentData.RESULT_COLUMN_PREFIX + objective
        results_df = exp_data.results
        plt.rcParams["figure.figsize"] = (10, 4)

        sns.scatterplot(
            x=results_df.trial_id, y=results_df[objective_column],
            alpha=0.7, label="Trial")  # Result of each trial
        sns.lineplot(
            x=results_df.trial_id, y=results_df[objective_column].cummin(),
            label="Incumbent")  # the best result so far (cummin)

        plt.yscale('log')

        plt.xlabel("Trial number")
        plt.ylabel(objective)

        plt.title("Optimizer Trends for Experiment: " + exp_data.exp_id)
        plt.grid()
        plt.show()  # type: ignore[no-untyped-call]


def ignore_plotter_warnings(plotter_method: MlosVizMethod = MlosVizMethod.AUTO) -> None:
    """
    Suppress some annoying warnings from third-party data visualization packages by
    adding them to the warnings filter.

    Parameters
    ----------
    plotter_method: MlosVizMethod
        The method to use for visualizing the experiment results.
    """
    warnings.filterwarnings("ignore", category=FutureWarning)

    if plotter_method == MlosVizMethod.DABL:
        import mlos_viz.dabl    # pylint: disable=import-outside-toplevel
        mlos_viz.dabl.ignore_plotter_warnings()
    else:
        raise NotImplementedError(f"Unhandled method: {plotter_method}")


def plot(exp_data: ExperimentData,
         plotter_method: MlosVizMethod = MlosVizMethod.AUTO,
         filter_warnings: bool = True) -> None:
    """
    Plots the results of the experiment.

    Intended to be used from a Jupyter notebook.

    Parameters
    ----------
    exp_data: ExperimentData
        The experiment data to plot.
    plotter_method: MlosVizMethod
        The method to use for visualizing the experiment results.
    filter_warnings: bool
        Whether or not to filter some warnings from the plotter.
    """
    _plot_optimizer_trends(exp_data)

    if filter_warnings:
        ignore_plotter_warnings(plotter_method)

    if MlosVizMethod.DABL:
        import mlos_viz.dabl    # pylint: disable=import-outside-toplevel
        mlos_viz.dabl.plot(exp_data)
    else:
        raise NotImplementedError(f"Unhandled method: {plotter_method}")

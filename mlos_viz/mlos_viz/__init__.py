#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
mlos_viz is a framework to help visualizing, explain, and gain insights from results
from the mlos_bench framework for benchmarking and optimization automation.
"""

from enum import Enum
from typing import Any

from mlos_bench.storage.base_experiment_data import ExperimentData
from mlos_viz import base


class MlosVizMethod(Enum):
    """
    What method to use for visualizing the experiment results.
    """

    DABL = "dabl"
    AUTO = DABL     # use dabl as the current default


def ignore_plotter_warnings(plotter_method: MlosVizMethod = MlosVizMethod.AUTO) -> None:
    """
    Suppress some annoying warnings from third-party data visualization packages by
    adding them to the warnings filter.

    Parameters
    ----------
    plotter_method: MlosVizMethod
        The method to use for visualizing the experiment results.
    """
    base.ignore_plotter_warnings()
    if plotter_method == MlosVizMethod.DABL:
        import mlos_viz.dabl    # pylint: disable=import-outside-toplevel
        mlos_viz.dabl.ignore_plotter_warnings()
    else:
        raise NotImplementedError(f"Unhandled method: {plotter_method}")


def plot(exp_data: ExperimentData,
         plotter_method: MlosVizMethod = MlosVizMethod.AUTO,
         filter_warnings: bool = True,
         **kwargs: Any) -> None:
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
    kwargs : dict
        Remaining keyword arguments are passed along to the underlying plotter(s).
    """
    if filter_warnings:
        ignore_plotter_warnings(plotter_method)

    base.plot_optimizer_trends(exp_data)
    top_n_config_args = {}
    for kword in exp_data.top_n_configs.__kwdefaults__:
        if kword in kwargs:
            top_n_config_args[kword] = kwargs[kword]
    base.plot_top_n_configs(exp_data, **kwargs)

    if MlosVizMethod.DABL:
        import mlos_viz.dabl    # pylint: disable=import-outside-toplevel
        mlos_viz.dabl.plot(exp_data)
    else:
        raise NotImplementedError(f"Unhandled method: {plotter_method}")

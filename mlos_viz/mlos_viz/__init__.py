#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
mlos_viz is a framework to help visualizing, explain, and gain insights from results
from the :py:mod:`mlos_bench` framework for benchmarking and optimization automation.

It can be installed from `pypi <https://pypi.org/project/mlos-viz>`_ via ``pip
install mlos-viz``.

Overview
++++++++

Its main entrypoint is the :py:func:`plot` function, which can be used to
automatically visualize :py:class:`~.ExperimentData` from :py:mod:`mlos_bench` using
other libraries for automatic data correlation and visualization like
:external:py:func:`dabl <dabl.plot>`.
"""

from enum import Enum
from typing import Any, Literal

import pandas

from mlos_bench.storage.base_experiment_data import ExperimentData
from mlos_viz import base
from mlos_viz.util import expand_results_data_args
from mlos_viz.version import VERSION

__version__ = VERSION


class MlosVizMethod(Enum):
    """What method to use for visualizing the experiment results."""

    DABL = "dabl"
    AUTO = DABL  # use dabl as the current default


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
        import mlos_viz.dabl  # pylint: disable=import-outside-toplevel

        mlos_viz.dabl.ignore_plotter_warnings()
    else:
        raise NotImplementedError(f"Unhandled method: {plotter_method}")


def plot(
    exp_data: ExperimentData | None = None,
    *,
    results_df: pandas.DataFrame | None = None,
    objectives: dict[str, Literal["min", "max"]] | None = None,
    plotter_method: MlosVizMethod = MlosVizMethod.AUTO,
    filter_warnings: bool = True,
    **kwargs: Any,
) -> None:
    """
    Plots the results of the experiment.

    Intended to be used from a Jupyter notebook.

    Parameters
    ----------
    exp_data: ExperimentData
        The experiment data to plot.
    results_df : pandas.DataFrame | None
        Optional `results_df` to plot.
        If not provided, defaults to :py:attr:`.ExperimentData.results_df` property.
    objectives : Optional[dict[str, Literal["min", "max"]]]
        Optional objectives to plot.
        If not provided, defaults to :py:attr:`.ExperimentData.objectives` property.
    plotter_method: MlosVizMethod
        The method to use for visualizing the experiment results.
    filter_warnings: bool
        Whether or not to filter some warnings from the plotter.
    kwargs : dict
        Remaining keyword arguments are passed along to the underlying plotter(s).
    """
    if filter_warnings:
        ignore_plotter_warnings(plotter_method)
    (results_df, _obj_cols) = expand_results_data_args(exp_data, results_df, objectives)

    base.plot_optimizer_trends(exp_data, results_df=results_df, objectives=objectives)
    base.plot_top_n_configs(exp_data, results_df=results_df, objectives=objectives, **kwargs)

    if MlosVizMethod.DABL:
        import mlos_viz.dabl  # pylint: disable=import-outside-toplevel

        mlos_viz.dabl.plot(exp_data, results_df=results_df, objectives=objectives)
    else:
        raise NotImplementedError(f"Unhandled method: {plotter_method}")

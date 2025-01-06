#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Small wrapper functions for plotting :py:mod:`mlos_bench` data via
:external:py:func:`dabl.plot`.

Notes
-----
See `dabl <https://dabl.github.io/stable/>`_ for more information on the dabl library.
"""
import warnings
from typing import Literal

import dabl
import pandas

from mlos_bench.storage.base_experiment_data import ExperimentData
from mlos_viz.util import expand_results_data_args


def plot(
    exp_data: ExperimentData | None = None,
    *,
    results_df: pandas.DataFrame | None = None,
    objectives: dict[str, Literal["min", "max"]] | None = None,
) -> None:
    """
    Plots the :py:class:`~mlos_bench.storage.base_storage.Storage.Experiment` results
    data using :external:py:func:`dabl.plot`.

    Parameters
    ----------
    exp_data : ExperimentData
        The ExperimentData (e.g., obtained from the storage layer) to plot.
    results_df : pandas.DataFrame | None
        Optional results_df to plot.
        If not provided, defaults to exp_data.results_df property.
    objectives : Optional[dict[str, Literal["min", "max"]]]
        Optional objectives to plot.
        If not provided, defaults to exp_data.objectives property.
    """
    (results_df, obj_cols) = expand_results_data_args(exp_data, results_df, objectives)
    for obj_col in obj_cols:
        dabl.plot(X=results_df, target_col=obj_col)


def ignore_plotter_warnings() -> None:
    """Add some filters to ignore warnings from the plotter."""
    # pylint: disable=import-outside-toplevel
    warnings.filterwarnings("ignore", category=FutureWarning)
    warnings.filterwarnings(
        "ignore",
        module="dabl",
        category=UserWarning,
        message="Could not infer format",
    )
    warnings.filterwarnings(
        "ignore",
        module="dabl",
        category=UserWarning,
        message="(Dropped|Discarding) .* outliers",
    )
    warnings.filterwarnings(
        "ignore",
        module="dabl",
        category=UserWarning,
        message="Not plotting highly correlated",
    )
    warnings.filterwarnings(
        "ignore",
        module="dabl",
        category=UserWarning,
        message="Missing values in target_col have been removed for regression",
    )
    from sklearn.exceptions import UndefinedMetricWarning

    warnings.filterwarnings(
        "ignore",
        module="sklearn",
        category=UndefinedMetricWarning,
        message="Recall is ill-defined",
    )
    warnings.filterwarnings(
        "ignore",
        category=DeprecationWarning,
        message="is_categorical_dtype is deprecated and will be removed in a future version.",
    )
    warnings.filterwarnings(
        "ignore",
        category=DeprecationWarning,
        module="sklearn",
        message="is_sparse is deprecated and will be removed in a future version.",
    )
    from matplotlib._api.deprecation import MatplotlibDeprecationWarning

    warnings.filterwarnings(
        "ignore",
        category=MatplotlibDeprecationWarning,
        module="dabl",
        message="The legendHandles attribute was deprecated in Matplotlib 3.7 and will be removed",
    )

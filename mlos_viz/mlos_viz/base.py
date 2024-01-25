#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Base functions for visualizing, explain, and gain insights from results.
"""

from typing import Any, Callable, Dict, List, Literal, Optional, Tuple

import warnings

from importlib.metadata import version
from matplotlib import pyplot as plt
import pandas
import seaborn as sns

from mlos_bench.storage.base_experiment_data import ExperimentData


_SEABORN_VERS = version('seaborn')


def get_kwarg_defaults(target: Callable, **kwargs: Any) -> Dict[str, Any]:
    """
    Assembles a smaller kwargs dict for the specified target function.

    Note: this only works with non-positional kwargs (e.g., those after a * arg).
    """
    target_kwargs = {}
    for kword in target.__kwdefaults__:     # or {} # intentionally omitted for now
        if kword in kwargs:
            target_kwargs[kword] = kwargs[kword]
    return target_kwargs


def ignore_plotter_warnings() -> None:
    """
    Suppress some annoying warnings from third-party data visualization packages by
    adding them to the warnings filter.
    """
    warnings.filterwarnings("ignore", category=FutureWarning)
    if _SEABORN_VERS <= '0.13.1':
        warnings.filterwarnings("ignore", category=DeprecationWarning, module="seaborn",    # but actually comes from pandas
                                message="is_categorical_dtype is deprecated and will be removed in a future version.")


def add_groupby_desc_column(results_df: pandas.DataFrame,
                            groupby_columns: Optional[List[str]] = None,
                            ) -> Tuple[pandas.DataFrame, List[str], str]:
    """
    Adds a group descriptor column to the results_df.

    Parameters
    ----------
    results_df: ExperimentData
        The experiment data to add the descriptor column to.
    groupby_columns: Optional[List[str]]
    """
    # Compose a new groupby_column for display purposes that is the
    # concatenation of the min trial_id (the first one) of each config trial
    # group and the config_id.
    # Note: It's need to be a string (e.g., categorical) for boxplot and lineplot to
    # be on the same axis anyways.
    if groupby_columns is None:
        groupby_columns = ["tunable_config_trial_group_id", "tunable_config_id"]
    groupby_column = ",".join(groupby_columns)
    results_df[groupby_column] = results_df[groupby_columns].astype(str).apply(
        lambda x: ",".join(x), axis=1)  # pylint: disable=unnecessary-lambda
    groupby_columns.append(groupby_column)
    return (results_df, groupby_columns, groupby_column)


def plot_optimizer_trends(
        exp_data: Optional[ExperimentData] = None, *,
        results_df: Optional[pandas.DataFrame] = None,
        objectives: Optional[Dict[str, Literal["min", "max"]]] = None,
) -> None:
    """
    Plots the optimizer trends for the Experiment.

    Parameters
    ----------
    exp_data : ExperimentData
        The ExperimentData (e.g., obtained from the storage layer) to plot.
    results_df : Optional["pandas.DataFrame"]
        Optional results_df to plot.
        If not provided, defaults to exp_data.results_df property.
    objectives : Optional[Dict[str, Literal["min", "max"]]]
        Optional objectives to plot.
        If not provided, defaults to exp_data.objectives property.
    """
    (results_df, obj_cols) = ExperimentData.expand_results_data_args(exp_data, results_df, objectives)
    (results_df, groupby_columns, groupby_column) = add_groupby_desc_column(results_df)

    for (objective_column, ascending) in obj_cols.items():
        incumbent_column = objective_column + ".incumbent"

        # Determine the mean of each config trial group to match the box plots.
        group_results_df = results_df.groupby(groupby_columns)[objective_column].mean()\
            .reset_index().sort_values(groupby_columns)
        #
        # Note: technically the optimizer (usually) uses the *first* result for a
        # given config trial group before moving on to a new config (x-axis), so
        # plotting the mean may be slightly misleading when trying to understand the
        # actual path taken by the optimizer in case of high variance samples.
        # Here's a way to do that, though it can also be misleading if the optimizer
        # later gets a worse value for that config group as well.
        #
        # group_results_df = results_df.sort_values(groupby_columns + ["trial_id"]).groupby(
        #   groupby_columns).head(1)[groupby_columns + [objective_column]].reset_index()

        # Calculate the incumbent (best seen so far)
        if ascending:
            group_results_df[incumbent_column] = group_results_df[objective_column].cummin()
        else:
            group_results_df[incumbent_column] = group_results_df[objective_column].cummax()

        plt.rcParams["figure.figsize"] = (10, 5)
        (_fig, ax) = plt.subplots()

        # Result of each set of trials for a config
        sns.boxplot(
            data=results_df,
            x=groupby_column,
            y=objective_column,
            ax=ax,
        )

        # Results of the best so far.
        ax = sns.lineplot(
            data=group_results_df,
            x=groupby_column,
            y=incumbent_column,
            alpha=0.7,
            label="Mean of Incumbent Config Trial Group",
            ax=ax,
        )

        plt.yscale('log')
        plt.ylabel(objective_column.replace(ExperimentData.RESULT_COLUMN_PREFIX, ""))

        plt.xlabel("Config Trial Group ID, Config ID")
        plt.xticks(rotation=90)

        plt.title("Optimizer Trends for Experiment: " + exp_data.experiment_id if exp_data is not None else "")
        plt.grid()
        plt.show()  # type: ignore[no-untyped-call]


def plot_top_n_configs(exp_data: Optional[ExperimentData] = None,
                       *,
                       results_df: Optional[pandas.DataFrame] = None,
                       objectives: Optional[Dict[str, Literal["min", "max"]]] = None,
                       with_scatter_plot: bool = False,
                       **kwargs: Any,
                       ) -> None:
    # pylint: disable=too-many-locals
    """
    Plots the top-N configs along with the default config for the given ExperimentData.

    Intended to be used from a Jupyter notebook.

    Parameters
    ----------
    exp_data: ExperimentData
        The experiment data to plot.
    results_df : Optional["pandas.DataFrame"]
        Optional results_df to plot.
        If not provided, defaults to exp_data.results_df property.
    objectives : Optional[Dict[str, Literal["min", "max"]]]
        Optional objectives to plot.
        If not provided, defaults to exp_data.objectives property.
    with_scatter_plot : bool
        Whether to also add scatter plot to the output figure.
    kwargs : dict
        Remaining keyword arguments are passed along to the ExperimentData.top_n_configs.
    """
    (results_df, _obj_cols) = ExperimentData.expand_results_data_args(exp_data, results_df, objectives)
    top_n_config_args = get_kwarg_defaults(ExperimentData.top_n_configs, **kwargs)
    if "results_df" not in top_n_config_args:
        top_n_config_args["results_df"] = results_df
    if "objectives" not in top_n_config_args:
        top_n_config_args["objectives"] = objectives
    (top_n_config_results_df, _top_n_config_ids, orderby_cols) = exp_data.top_n_configs(**top_n_config_args)

    (top_n_config_results_df, _groupby_columns, groupby_column) = add_groupby_desc_column(top_n_config_results_df)
    top_n = len(top_n_config_results_df[groupby_column].unique()) - 1

    for (orderby_col, ascending) in orderby_cols.items():
        opt_tgt = orderby_col.replace(ExperimentData.RESULT_COLUMN_PREFIX, "")
        (_fig, ax) = plt.subplots()
        sns.violinplot(
            data=top_n_config_results_df,
            x=groupby_column,
            y=orderby_col,
            ax=ax,
        )
        if with_scatter_plot:
            sns.scatterplot(
                data=top_n_config_results_df,
                x=groupby_column,
                y=orderby_col,
                legend=None,
                ax=ax,
            )
        plt.grid()
        (xticks, xlabels) = plt.xticks()
        # default should be in the first position based on top_n_configs() return
        xlabels[0] = "default"          # type: ignore[call-overload]
        plt.xticks(xticks, xlabels)     # type: ignore[arg-type]
        plt.xlabel("Config Trial Group, Config ID")
        plt.xticks(rotation=90)
        plt.ylabel(opt_tgt)
        plt.yscale('log')
        extra_title = "(lower is better)" if ascending else "(lower is better)"
        plt.title(f"Top {top_n} configs {opt_tgt} {extra_title}")
        plt.show()  # type: ignore[no-untyped-call]

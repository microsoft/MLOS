#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
mlos_viz is a framework to help visualizing, explain, and gain insights from results
from the mlos_bench framework for benchmarking and optimization automation.
"""

from typing import Any, Callable, Dict

import warnings

from importlib.metadata import version
from matplotlib import pyplot as plt
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


def plot_optimizer_trends(exp_data: ExperimentData) -> None:
    """
    Plots the optimizer trends for the Experiment.

    Intended to be used from a Jupyter notebook.

    Parameters
    ----------
    exp_data: ExperimentData
        The experiment data to plot.
    """
    results_df = exp_data.results_df
    groupby_columns = ["tunable_config_trial_group_id", "tunable_config_id"]
    groupby_column = ",".join(groupby_columns)
    for (objective, direction) in exp_data.objectives.items():
        objective_column = ExperimentData.RESULT_COLUMN_PREFIX + objective
        incumbent_column = objective_column + ".incumbent"

        # Compose a new groupby_column for display purposes that is the
        # concatenation of the min trial_id (the first one) of each config trial
        # group and the config_id.
        # Note: It's need to be a string (e.g., categorical) for boxplot and lineplot to be on the same axis anyways.
        results_df[groupby_column] = results_df[groupby_columns].astype(str).apply(lambda x: ",".join(x), axis=1)
        groupby_columns.append(groupby_column)

        # Determine the mean of each config trial group to match the box plots.
        group_results_df = results_df.groupby(groupby_columns)[objective_column].mean().reset_index().sort_values(groupby_columns)
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
        if direction == "min":
            group_results_df[incumbent_column] = group_results_df[objective_column].cummin()
        elif direction == "max":
            group_results_df[incumbent_column] = group_results_df[objective_column].cummax()
        else:
            raise ValueError(f"Unhandled direction {direction} for target {objective}")

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
        plt.ylabel(objective)

        plt.xlabel("Config Trial Group ID, Config ID")
        plt.xticks(rotation=90)

        plt.title("Optimizer Trends for Experiment: " + exp_data.experiment_id)
        plt.grid()
        plt.show()  # type: ignore[no-untyped-call]


def plot_top_n_configs(exp_data: ExperimentData, with_scatter_plot: bool = False, **kwargs: Any) -> None:
    """
    Plots the top-N configs along with the default config for the given ExperimentData.

    Intended to be used from a Jupyter notebook.

    Parameters
    ----------
    exp_data: ExperimentData
        The experiment data to plot.
    with_scatter_plot : bool
        Whether to also add scatter plot to the output figure.
    kwargs : dict
        Remaining keyword arguments are passed along to the ExperimentData.top_n_configs.
    """
    top_n_config_args = get_kwarg_defaults(ExperimentData.top_n_configs, **kwargs)
    (top_n_config_results_df, top_n_config_ids, opt_target, opt_direction) = exp_data.top_n_configs(**top_n_config_args)
    top_n = len(top_n_config_results_df["config_id"].unique()) - 1
    target_column = ExperimentData.RESULT_COLUMN_PREFIX + opt_target
    (_fig, ax) = plt.subplots()
    sns.boxplot(
        data=top_n_config_results_df,
        y=target_column,
    )
    if with_scatter_plot:
        sns.scatterplot(
            data=top_n_config_results_df,
            y=target_column,
            legend=None,
            ax=ax,
        )
    plt.grid()
    (xticks, xlabels) = plt.xticks()
    # default should be in the first position based on top_n_configs() return
    xlabels[0] = "default"          # type: ignore[call-overload]
    plt.xticks(xticks, xlabels)     # type: ignore[arg-type]
    plt.xlabel("Configuration")
    plt.xticks(rotation=90)
    plt.ylabel(opt_target)
    extra_title = "(higher is better)" if opt_direction == "max" else "(lower is better)"
    plt.title(f"Top {top_n} configs {opt_target} {extra_title}")
    plt.show()  # type: ignore[no-untyped-call]

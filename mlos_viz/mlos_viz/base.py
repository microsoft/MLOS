#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Base functions for visualizing, explain, and gain insights from results."""

import re
import warnings
from importlib.metadata import version
from typing import Any, Callable, Dict, Iterable, List, Literal, Optional, Tuple, Union

import pandas
import seaborn as sns
from matplotlib import pyplot as plt
from pandas.api.types import is_numeric_dtype
from pandas.core.groupby.generic import SeriesGroupBy

from mlos_bench.storage.base_experiment_data import ExperimentData
from mlos_viz.util import expand_results_data_args

_SEABORN_VERS = version("seaborn")


def _get_kwarg_defaults(target: Callable, **kwargs: Any) -> Dict[str, Any]:
    """
    Assembles a smaller kwargs dict for the specified target function.

    Note: this only works with non-positional kwargs (e.g., those after a * arg).
    """
    target_kwargs = {}
    for kword in target.__kwdefaults__:  # or {} # intentionally omitted for now
        if kword in kwargs:
            target_kwargs[kword] = kwargs[kword]
    return target_kwargs


def ignore_plotter_warnings() -> None:
    """Suppress some annoying warnings from third-party data visualization packages by
    adding them to the warnings filter.
    """
    warnings.filterwarnings("ignore", category=FutureWarning)
    if _SEABORN_VERS <= "0.13.1":
        warnings.filterwarnings(
            "ignore",
            category=DeprecationWarning,
            module="seaborn",  # but actually comes from pandas
            message="is_categorical_dtype is deprecated and will be removed in a future version.",
        )


def _add_groupby_desc_column(
    results_df: pandas.DataFrame,
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
    results_df[groupby_column] = (
        results_df[groupby_columns].astype(str).apply(lambda x: ",".join(x), axis=1)
    )  # pylint: disable=unnecessary-lambda
    groupby_columns.append(groupby_column)
    return (results_df, groupby_columns, groupby_column)


def augment_results_df_with_config_trial_group_stats(
    exp_data: Optional[ExperimentData] = None,
    *,
    results_df: Optional[pandas.DataFrame] = None,
    requested_result_cols: Optional[Iterable[str]] = None,
) -> pandas.DataFrame:
    # pylint: disable=too-complex
    """
    Add a number of useful statistical measure columns to the results dataframe.

    In particular, for each numeric result, we add the following columns for each
    requested result column:

    - ".p50": the median of each config trial group results

    - ".p75": the p75 of each config trial group results

    - ".p90": the p90 of each config trial group results

    - ".p95": the p95 of each config trial group results

    - ".p99": the p95 of each config trial group results

    - ".mean": the mean of each config trial group results

    - ".stddev": the mean of each config trial group results

    - ".var": the variance of each config trial group results

    - ".var_zscore": the zscore of this group (i.e., variance relative to the stddev
      of all group variances). This can be useful for filtering out outliers (e.g.,
      configs with high variance relative to others by restricting to abs < 2 to
      remove those two standard deviations from the mean variance across all config
      trial groups).

    Additionally, we add a "tunable_config_trial_group_size" column that indicates
    the number of trials using a particular config.

    Parameters
    ----------
    exp_data : ExperimentData
        The ExperimentData (e.g., obtained from the storage layer) to plot.
    results_df : Optional[pandas.DataFrame]
        The results dataframe to augment, by default None to use the results_df property.
    requested_result_cols : Optional[Iterable[str]]
        Which results columns to augment, by default None to use all results columns
        that look numeric.

    Returns
    -------
    pandas.DataFrame
        The augmented results dataframe.
    """
    if results_df is None:
        if exp_data is None:
            raise ValueError("Either exp_data or results_df must be provided.")
        results_df = exp_data.results_df
    results_groups = results_df.groupby("tunable_config_id")
    if len(results_groups) <= 1:
        raise ValueError(f"Not enough data: {len(results_groups)}")

    if requested_result_cols is None:
        result_cols = set(
            col
            for col in results_df.columns
            if col.startswith(ExperimentData.RESULT_COLUMN_PREFIX)
        )
    else:
        result_cols = set(
            col
            for col in requested_result_cols
            if col.startswith(ExperimentData.RESULT_COLUMN_PREFIX) and col in results_df.columns
        )
        result_cols.update(
            set(
                ExperimentData.RESULT_COLUMN_PREFIX + col
                for col in requested_result_cols
                if ExperimentData.RESULT_COLUMN_PREFIX in results_df.columns
            )
        )

    def compute_zscore_for_group_agg(
        results_groups_perf: "SeriesGroupBy",
        stats_df: pandas.DataFrame,
        result_col: str,
        agg: Union[Literal["mean"], Literal["var"], Literal["std"]],
    ) -> None:
        results_groups_perf_aggs = results_groups_perf.agg(agg)  # TODO: avoid recalculating?
        # Compute the zscore of the chosen aggregate performance of each group into
        # each row in the dataframe.
        stats_df[result_col + f".{agg}_mean"] = results_groups_perf_aggs.mean()
        stats_df[result_col + f".{agg}_stddev"] = results_groups_perf_aggs.std()
        stats_df[result_col + f".{agg}_zscore"] = (
            stats_df[result_col + f".{agg}"] - stats_df[result_col + f".{agg}_mean"]
        ) / stats_df[result_col + f".{agg}_stddev"]
        stats_df.drop(
            columns=[result_col + ".var_" + agg for agg in ("mean", "stddev")], inplace=True
        )

    augmented_results_df = results_df
    augmented_results_df["tunable_config_trial_group_size"] = results_groups["trial_id"].transform(
        "count"
    )
    for result_col in result_cols:
        if not result_col.startswith(ExperimentData.RESULT_COLUMN_PREFIX):
            continue
        if re.search(r"(start|end).*time", result_col, flags=re.IGNORECASE):
            # Ignore computing variance on things like that look like timestamps.
            continue
        if not is_numeric_dtype(results_df[result_col]):
            continue
        if results_df[result_col].unique().size == 1:
            continue
        results_groups_perf = results_groups[result_col]
        stats_df = pandas.DataFrame()
        stats_df[result_col + ".mean"] = results_groups_perf.transform("mean", numeric_only=True)
        stats_df[result_col + ".var"] = results_groups_perf.transform("var")
        stats_df[result_col + ".stddev"] = stats_df[result_col + ".var"].apply(lambda x: x**0.5)

        compute_zscore_for_group_agg(results_groups_perf, stats_df, result_col, "var")
        quantiles = [0.50, 0.75, 0.90, 0.95, 0.99]
        for quantile in quantiles:  # TODO: can we do this in one pass?
            quantile_col = f"{result_col}.p{int(quantile * 100)}"
            stats_df[quantile_col] = results_groups_perf.transform("quantile", quantile)
        augmented_results_df = pandas.concat([augmented_results_df, stats_df], axis=1)
    return augmented_results_df


def limit_top_n_configs(
    exp_data: Optional[ExperimentData] = None,
    *,
    results_df: Optional[pandas.DataFrame] = None,
    objectives: Optional[Dict[str, Literal["min", "max"]]] = None,
    top_n_configs: int = 10,
    method: Literal["mean", "p50", "p75", "p90", "p95", "p99"] = "mean",
) -> Tuple[pandas.DataFrame, List[int], Dict[str, bool]]:
    # pylint: disable=too-many-locals
    """
    Utility function to process the results and determine the best performing configs
    including potential repeats to help assess variability.

    Parameters
    ----------
    exp_data : Optional[ExperimentData]
        The ExperimentData (e.g., obtained from the storage layer) to operate on.
    results_df : Optional[pandas.DataFrame]
        The results dataframe to augment, by default None to use the results_df property.
    objectives : Iterable[str], optional
        Which result column(s) to use for sorting the configs, and in which
        direction ("min" or "max").
        By default None to automatically select the experiment objectives.
    top_n_configs : int, optional
        How many configs to return, including the default, by default 20.
    method: Literal["mean", "median", "p50", "p75", "p90", "p95", "p99"] = "mean",
        Which statistical method to use when sorting the config groups before
        determining the cutoff, by default "mean".

    Returns
    -------
    (top_n_config_results_df, top_n_config_ids, orderby_cols) :
    Tuple[pandas.DataFrame, List[int], Dict[str, bool]]
        The filtered results dataframe, the config ids, and the columns used to
        order the configs.
    """
    # Do some input checking first.
    if method not in ["mean", "median", "p50", "p75", "p90", "p95", "p99"]:
        raise ValueError(f"Invalid method: {method}")

    # Prepare the orderby columns.
    (results_df, objs_cols) = expand_results_data_args(
        exp_data,
        results_df=results_df,
        objectives=objectives,
    )
    assert isinstance(results_df, pandas.DataFrame)

    # Augment the results dataframe with some useful stats.
    results_df = augment_results_df_with_config_trial_group_stats(
        exp_data=exp_data,
        results_df=results_df,
        requested_result_cols=objs_cols.keys(),
    )
    # Note: mypy seems to lose its mind for some reason and keeps forgetting that
    # results_df is not None and is in fact a DataFrame, so we periodically assert
    # it in this func for now.
    assert results_df is not None
    orderby_cols: Dict[str, bool] = {
        obj_col + f".{method}": ascending for (obj_col, ascending) in objs_cols.items()
    }

    config_id_col = "tunable_config_id"
    group_id_col = "tunable_config_trial_group_id"  # first trial_id per config group
    trial_id_col = "trial_id"

    default_config_id = (
        results_df[trial_id_col].min() if exp_data is None else exp_data.default_tunable_config_id
    )
    assert default_config_id is not None, "Failed to determine default config id."

    # Filter out configs whose variance is too large.
    # But also make sure the default configs is still in the resulting dataframe
    # (for comparison purposes).
    for obj_col in objs_cols:
        assert results_df is not None
        if method == "mean":
            singletons_mask = results_df["tunable_config_trial_group_size"] == 1
        else:
            singletons_mask = results_df["tunable_config_trial_group_size"] > 1
        results_df = results_df.loc[
            (
                (results_df[f"{obj_col}.var_zscore"].abs() < 2)
                | (singletons_mask)
                | (results_df[config_id_col] == default_config_id)
            )
        ]
    assert results_df is not None

    # Also, filter results that are worse than the default.
    default_config_results_df = results_df.loc[results_df[config_id_col] == default_config_id]
    for orderby_col, ascending in orderby_cols.items():
        default_vals = default_config_results_df[orderby_col].unique()
        assert len(default_vals) == 1
        default_val = default_vals[0]
        assert results_df is not None
        if ascending:
            results_df = results_df.loc[(results_df[orderby_col] <= default_val)]
        else:
            results_df = results_df.loc[(results_df[orderby_col] >= default_val)]

    # Now regroup and filter to the top-N configs by their group performance dimensions.
    assert results_df is not None
    group_results_df: pandas.DataFrame = results_df.groupby(config_id_col).first()[
        orderby_cols.keys()
    ]
    top_n_config_ids: List[int] = (
        group_results_df.sort_values(
            by=list(orderby_cols.keys()), ascending=list(orderby_cols.values())
        )
        .head(top_n_configs)
        .index.tolist()
    )

    # Remove the default config if it's included. We'll add it back later.
    if default_config_id in top_n_config_ids:
        top_n_config_ids.remove(default_config_id)
    # Get just the top-n config results.
    # Sort by the group ids.
    top_n_config_results_df = results_df.loc[
        (results_df[config_id_col].isin(top_n_config_ids))
    ].sort_values([group_id_col, config_id_col, trial_id_col])
    # Place the default config at the top of the list.
    top_n_config_ids.insert(0, default_config_id)
    top_n_config_results_df = pandas.concat(
        [default_config_results_df, top_n_config_results_df],
        axis=0,
    )
    return (top_n_config_results_df, top_n_config_ids, orderby_cols)


def plot_optimizer_trends(
    exp_data: Optional[ExperimentData] = None,
    *,
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
    (results_df, obj_cols) = expand_results_data_args(exp_data, results_df, objectives)
    (results_df, groupby_columns, groupby_column) = _add_groupby_desc_column(results_df)

    for objective_column, ascending in obj_cols.items():
        incumbent_column = objective_column + ".incumbent"

        # Determine the mean of each config trial group to match the box plots.
        group_results_df = (
            results_df.groupby(groupby_columns)[objective_column]
            .mean()
            .reset_index()
            .sort_values(groupby_columns)
        )
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

        (_fig, axis) = plt.subplots(figsize=(15, 5))

        # Result of each set of trials for a config
        sns.boxplot(
            data=results_df,
            x=groupby_column,
            y=objective_column,
            ax=axis,
        )

        # Results of the best so far.
        axis = sns.lineplot(
            data=group_results_df,
            x=groupby_column,
            y=incumbent_column,
            alpha=0.7,
            label="Mean of Incumbent Config Trial Group",
            ax=axis,
        )

        plt.yscale("log")
        plt.ylabel(objective_column.replace(ExperimentData.RESULT_COLUMN_PREFIX, ""))

        plt.xlabel("Config Trial Group ID, Config ID")
        plt.xticks(rotation=90, fontsize=8)

        plt.title(
            "Optimizer Trends for Experiment: " + exp_data.experiment_id
            if exp_data is not None
            else ""
        )
        plt.grid()
        plt.show()  # type: ignore[no-untyped-call]


def plot_top_n_configs(
    exp_data: Optional[ExperimentData] = None,
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
        Remaining keyword arguments are passed along to the limit_top_n_configs function.
    """
    (results_df, _obj_cols) = expand_results_data_args(exp_data, results_df, objectives)
    top_n_config_args = _get_kwarg_defaults(limit_top_n_configs, **kwargs)
    if "results_df" not in top_n_config_args:
        top_n_config_args["results_df"] = results_df
    if "objectives" not in top_n_config_args:
        top_n_config_args["objectives"] = objectives
    (top_n_config_results_df, _top_n_config_ids, orderby_cols) = limit_top_n_configs(
        exp_data=exp_data,
        **top_n_config_args,
    )

    (top_n_config_results_df, _groupby_columns, groupby_column) = _add_groupby_desc_column(
        top_n_config_results_df,
    )
    top_n = len(top_n_config_results_df[groupby_column].unique()) - 1

    for orderby_col, ascending in orderby_cols.items():
        opt_tgt = orderby_col.replace(ExperimentData.RESULT_COLUMN_PREFIX, "")
        (_fig, axis) = plt.subplots()
        sns.violinplot(
            data=top_n_config_results_df,
            x=groupby_column,
            y=orderby_col,
            ax=axis,
        )
        if with_scatter_plot:
            sns.scatterplot(
                data=top_n_config_results_df,
                x=groupby_column,
                y=orderby_col,
                legend=None,
                ax=axis,
            )
        plt.grid()
        (xticks, xlabels) = plt.xticks()
        # default should be in the first position based on top_n_configs() return
        xlabels[0] = "default"  # type: ignore[call-overload]
        plt.xticks(xticks, xlabels)  # type: ignore[arg-type]
        plt.xlabel("Config Trial Group, Config ID")
        plt.xticks(rotation=90)
        plt.ylabel(opt_tgt)
        plt.yscale("log")
        extra_title = "(lower is better)" if ascending else "(lower is better)"
        plt.title(f"Top {top_n} configs {opt_tgt} {extra_title}")
        plt.show()  # type: ignore[no-untyped-call]

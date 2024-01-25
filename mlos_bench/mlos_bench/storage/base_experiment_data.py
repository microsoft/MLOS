#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Base interface for accessing the stored benchmark experiment data.
"""

from abc import ABCMeta, abstractmethod
from distutils.util import strtobool    # pylint: disable=deprecated-module
from typing import Dict, List, Literal, Optional, Iterable, Tuple, Union, TYPE_CHECKING

import re

import pandas
from pandas.api.types import is_numeric_dtype

from mlos_bench.storage.base_tunable_config_data import TunableConfigData

if TYPE_CHECKING:
    from pandas.core.groupby.generic import SeriesGroupBy
    from mlos_bench.storage.base_trial_data import TrialData
    from mlos_bench.storage.base_tunable_config_trial_group_data import TunableConfigTrialGroupData


class ExperimentData(metaclass=ABCMeta):
    """
    Base interface for accessing the stored experiment benchmark data.

    An experiment groups together a set of trials that are run with a given set of
    scripts and mlos_bench configuration files.
    """

    RESULT_COLUMN_PREFIX = "result."
    CONFIG_COLUMN_PREFIX = "config."

    def __init__(self, *,
                 experiment_id: str,
                 description: str,
                 root_env_config: str,
                 git_repo: str,
                 git_commit: str):
        self._experiment_id = experiment_id
        self._description = description
        self._root_env_config = root_env_config
        self._git_repo = git_repo
        self._git_commit = git_commit

    @property
    def experiment_id(self) -> str:
        """
        ID of the experiment.
        """
        return self._experiment_id

    @property
    def description(self) -> str:
        """
        Description of the experiment.
        """
        return self._description

    @property
    def root_env_config(self) -> Tuple[str, str, str]:
        """
        Root environment configuration.

        Returns
        -------
        root_env_config : Tuple[str, str, str]
            A tuple of (root_env_config, git_repo, git_commit) for the root environment.
        """
        return (self._root_env_config, self._git_repo, self._git_commit)

    def __repr__(self) -> str:
        return f"Experiment :: {self._experiment_id}: '{self._description}'"

    @property
    @abstractmethod
    def objectives(self) -> Dict[str, Literal["min", "max"]]:
        """
        Retrieve the experiment's objectives data from the storage.

        Returns
        -------
        objectives : Dict[str, objective]
            A dictionary of the experiment's objective names (optimization_targets)
            and their directions (e.g., min or max).
        """

    @property
    @abstractmethod
    def trials(self) -> Dict[int, "TrialData"]:
        """
        Retrieve the experiment's trials' data from the storage.

        Returns
        -------
        trials : Dict[int, TrialData]
            A dictionary of the trials' data, keyed by trial id.
        """

    @property
    @abstractmethod
    def tunable_configs(self) -> Dict[int, TunableConfigData]:
        """
        Retrieve the experiment's (tunable) configs' data from the storage.

        Returns
        -------
        trials : Dict[int, TunableConfigData]
            A dictionary of the configs' data, keyed by (tunable) config id.
        """

    @property
    @abstractmethod
    def tunable_config_trial_groups(self) -> Dict[int, "TunableConfigTrialGroupData"]:
        """
        Retrieve the Experiment's (Tunable) Config Trial Group data from the storage.

        Returns
        -------
        trials : Dict[int, TunableConfigTrialGroupData]
            A dictionary of the trials' data, keyed by (tunable) by config id.
        """

    @property
    def default_tunable_config_id(self) -> Optional[int]:
        """
        Retrieves the (tunable) config id for the default tunable values for this experiment.

        Note: this is by *default* the first trial executed for this experiment.
        However, it is currently possible that the user changed the tunables config
        in between resumptions of an experiment.

        Returns
        -------
        int
        """
        # Note: this implementation is quite inefficient and may be better
        # reimplemented by subclasses.

        # Check to see if we included it in trial metadata.
        trials_items = sorted(self.trials.items())
        if not trials_items:
            return None
        for (_trial_id, trial) in trials_items:
            # Take the first config id marked as "defaults" when it was instantiated.
            if strtobool(str(trial.metadata_dict.get('is_defaults', False))):
                return trial.tunable_config_id
        # Fallback (min trial_id)
        return trials_items[0][1].tunable_config_id

    @property
    @abstractmethod
    def results_df(self) -> pandas.DataFrame:
        """
        Retrieve all experimental results as a single DataFrame.

        Returns
        -------
        results : pandas.DataFrame
            A DataFrame with configurations and results from all trials of the experiment.
            Has columns [trial_id, tunable_config_id, tunable_config_trial_group_id, ts_start, ts_end, status]
            followed by tunable config parameters (prefixed with "config.") and
            trial results (prefixed with "result."). The latter can be NULLs if the
            trial was not successful.
        """

    def augment_results_df_with_config_trial_group_stats(self, *,
                                                         results_df: Optional[pandas.DataFrame] = None,
                                                         requested_result_cols: Optional[Iterable[str]] = None,
                                                         ) -> pandas.DataFrame:
        # pylint: disable=too-complex
        """
        Add a number of useful statistical measure columns to the results dataframe.

        In particular, for each numeric result, we add the following columns:
            ".p50" - the median of each config trial group results
            ".p75" - the p75 of each config trial group results
            ".p90" - the p90 of each config trial group results
            ".p95" - the p95 of each config trial group results
            ".p99" - the p95 of each config trial group results
            ".mean" - the mean of each config trial group results
            ".stddev" - the mean of each config trial group results
            ".var" - the variance of each config trial group results
            ".var_zscore" - the zscore of this group (i.e., variance relative to the stddev of all group variances)
                This can be useful for filtering out outliers
                (e.g., configs with high variance relative to others by restricting to abs <= 2)

        Parameters
        ----------
        results_df : Optional[pandas.DataFrame]
            The results dataframe to augment, by default None to use the results_df property.
        requested_result_cols : Optional[Iterable[str]]
            Which results columns to augment, by default None to use all results columns.

        Returns
        -------
        pandas.DataFrame
            The augmented results dataframe.
        """
        if results_df is None:
            results_df = self.results_df
        results_groups = results_df.groupby("tunable_config_id")
        if len(results_groups) <= 1:
            raise ValueError(f"Not enough data: {len(results_groups)}")

        if requested_result_cols is None:
            result_cols = set(col for col in results_df.columns if col.startswith(self.RESULT_COLUMN_PREFIX))
        else:
            result_cols = set(col for col in requested_result_cols
                              if col.startswith(self.RESULT_COLUMN_PREFIX) and col in results_df.columns)
            result_cols.update(set(self.RESULT_COLUMN_PREFIX + col for col in requested_result_cols
                                   if self.RESULT_COLUMN_PREFIX in results_df.columns))

        def compute_zscore_for_group_agg(
                results_groups_perf: "SeriesGroupBy",
                stats_df: pandas.DataFrame,
                result_col: str,
                agg: Union[Literal["mean"], Literal["var"], Literal["std"]]
        ) -> None:
            results_groups_perf_aggs = results_groups_perf.agg(agg)    # TODO: avoid recalculating?
            # Compute the zscore of the chosen aggregate performance of each group into each row in the dataframe.
            stats_df[result_col + f".{agg}_mean"] = results_groups_perf_aggs.mean()
            stats_df[result_col + f".{agg}_stddev"] = results_groups_perf_aggs.std()
            stats_df[result_col + f".{agg}_zscore"] = \
                (stats_df[result_col + f".{agg}"] - stats_df[result_col + f".{agg}_mean"]) \
                / stats_df[result_col + f".{agg}_stddev"]
            stats_df.drop(columns=[result_col + ".var_" + agg for agg in ("mean", "stddev")], inplace=True)

        augmented_results_df = results_df
        for result_col in result_cols:
            if not result_col.startswith(self.RESULT_COLUMN_PREFIX):
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
            for quantile in quantiles:     # TODO: can we do this in one pass?
                quantile_col = result_col + f".p{int(quantile*100)}"
                stats_df[quantile_col] = results_groups_perf.transform("quantile", quantile)
            augmented_results_df = pandas.concat([augmented_results_df, stats_df], axis=1)
        return augmented_results_df

    @staticmethod
    def expand_results_data_args(
        exp_data: Optional["ExperimentData"] = None,
        results_df: Optional[pandas.DataFrame] = None,
        objectives: Optional[Dict[str, Literal["min", "max"]]] = None,
    ) -> Tuple[pandas.DataFrame, Dict[str, bool]]:
        """
        Expands some common arguments for working with results data.

        Used by mlos_viz as well.

        Parameters
        ----------
        exp_data : Optional[ExperimentData], optional
            ExperimentData to operate on.
        results_df : Optional[pandas.DataFrame], optional
            Optional results_df argument.
            Defaults to exp_data.results_df property.
        objectives : Optional[Dict[str, Literal["min", "max"]]], optional
            Optional objectives set to operate on.
            Defaults to exp_data.objectives property.

        Returns
        -------
        Tuple[pandas.DataFrame, Dict[str, bool]]
            The results dataframe and the objectives columns in the dataframe, plus whether or not they are in ascending order.
        """
        # Prepare the orderby columns.
        if results_df is None:
            if exp_data is None:
                raise ValueError("Must provide either exp_data or both results_df and objectives.")
            results_df = exp_data.results_df

        if objectives is None:
            if exp_data is None:
                raise ValueError("Must provide either exp_data or both results_df and objectives.")
            objectives = exp_data.objectives
        objs_cols: Dict[str, bool] = {}
        for (opt_tgt, opt_dir) in objectives.items():
            if opt_dir not in ["min", "max"]:
                raise ValueError(f"Unexpected optimization direction for target {opt_tgt}: {opt_dir}")
            ascending = opt_dir == "min"
            if opt_tgt.startswith(ExperimentData.RESULT_COLUMN_PREFIX) and opt_tgt in results_df.columns:
                objs_cols[opt_tgt] = ascending
            elif ExperimentData.RESULT_COLUMN_PREFIX + opt_tgt in results_df.columns:
                objs_cols[ExperimentData.RESULT_COLUMN_PREFIX + opt_tgt] = ascending
            else:
                raise UserWarning(f"{opt_tgt} is not a result column for experiment {exp_data}")
        return (results_df, objs_cols)

    def top_n_configs(self,
                      *,
                      results_df: Optional[pandas.DataFrame] = None,
                      top_n_configs: int = 10,
                      objectives: Optional[Dict[str, Literal["min", "max"]]] = None,
                      method: Literal["mean", "p50", "p75", "p90", "p95", "p99"] = "mean",
                      ) -> Tuple[pandas.DataFrame, List[int], Dict[str, bool]]:
        # pylint: disable=too-complex
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        """
        Utility function to process the results and determine the best performing
        configs including potential repeats to help assess variability.

        Parameters
        ----------
        results_df : Optional[pandas.DataFrame]
            The results dataframe to augment, by default None to use the results_df property.
        top_n_configs : int, optional
            How many configs to return, including the default, by default 20.
        objectives : Iterable[str], optional
            Which result column(s) to use for sorting the configs, and in which direction ("min" or "max").
            By default None to automatically select the experiment objectives.
        method: Literal["mean", "median", "p50", "p75", "p90", "p95", "p99"] = "mean",
            Which statistical method to use when sorting the config groups before determining the cutoff, by default "mean".

        Returns
        -------
        (top_n_config_results_df, top_n_config_ids, orderby_cols) : Tuple[pandas.DataFrame, List[int], Dict[str, bool]]
            The filtered results dataframe, the config ids, and the columns used to order the configs.
        """
        # Do some input checking first.
        if method not in ["mean", "median", "p50", "p75", "p90", "p95", "p99"]:
            raise ValueError(f"Invalid method: {method}")

        # Prepare the orderby columns.
        (results_df, objs_cols) = ExperimentData.expand_results_data_args(self, results_df=results_df, objectives=objectives)

        # Augment the results dataframe with some useful stats.
        results_df = self.augment_results_df_with_config_trial_group_stats(
            results_df=results_df,
            requested_result_cols=objs_cols.keys(),
        )
        orderby_cols: Dict[str, bool] = {obj_col + f".{method}": ascending for (obj_col, ascending) in objs_cols.items()}

        config_id_col = "tunable_config_id"
        group_id_col = "tunable_config_trial_group_id"     # first trial_id per config group
        trial_id_col = "trial_id"

        default_config_id = self.default_tunable_config_id
        assert default_config_id is not None, "Failed to determine default config id."

        # Filter out configs whose variance is too large.
        # But also make sure the default configs is still in the resulting dataframe
        # (for comparison purposes).
        for obj_col in objs_cols:
            results_df = results_df.loc[(
                (results_df[f"{obj_col}.var_zscore"] < 2)
                | (results_df[config_id_col] == default_config_id)
            )]

        # Also, filter results that are worse than the default.
        default_config_results_df = results_df.loc[results_df[config_id_col] == default_config_id]
        for (orderby_col, ascending) in orderby_cols.items():
            default_vals = default_config_results_df[orderby_col].unique()
            assert len(default_vals) == 1
            default_val = default_vals[0]
            if ascending:
                results_df = results_df.loc[(results_df[orderby_col] <= default_val)]
            else:
                results_df = results_df.loc[(results_df[orderby_col] >= default_val)]

        # Now regroup and filter to the top-N configs by their group performance dimensions.
        group_results_df: pandas.DataFrame = results_df.groupby(config_id_col).first()[orderby_cols.keys()]
        top_n_config_ids: List[int] = group_results_df.sort_values(
            by=list(orderby_cols.keys()), ascending=list(orderby_cols.values())).head(top_n_configs).index.tolist()

        # Remove the default config if it's included. We'll add it back later.
        if default_config_id in top_n_config_ids:
            top_n_config_ids.remove(default_config_id)
        # Get just the top-n config results.
        # Sort by the group ids.
        top_n_config_results_df = results_df.loc[(
            results_df[config_id_col].isin(top_n_config_ids)
        )].sort_values([group_id_col, config_id_col, trial_id_col])
        # Place the default config at the top of the list.
        top_n_config_ids.insert(0, default_config_id)
        top_n_config_results_df = pandas.concat([default_config_results_df, top_n_config_results_df], axis=0)
        return (top_n_config_results_df, top_n_config_ids, orderby_cols)

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
    def objectives(self) -> Dict[str, str]:
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

    def augment_results_df_with_config_trial_group_stats(
            self, requested_result_cols: Optional[Iterable[str]] = None) -> pandas.DataFrame:
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
        requested_result_cols : Optional[Iterable[str]]
            Which results columns to augment, by default None to use all results columns.

        Returns
        -------
        pandas.DataFrame
            The augmented results dataframe.
        """
        results_df = self.results_df
        results_groups = results_df.groupby("tunable_config_id")
        if requested_result_cols is None:
            result_cols = set(results_df.columns)
        else:
            result_cols = set(col for col in requested_result_cols if col in results_df.columns)
            result_cols.update(set(self.RESULT_COLUMN_PREFIX + col
                                   for col in requested_result_cols if self.RESULT_COLUMN_PREFIX in results_df.columns))
        if len(results_groups) <= 1:
            raise ValueError(f"Not enough data: {len(results_groups)}")

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

    def top_n_configs(self,
                      *,
                      top_n_configs: int = 20,
                      objective_name: Optional[str] = None,
                      method: Union[Literal["mean", "median"], float] = "mean",
                      ) -> Tuple[pandas.DataFrame, List[int], str, str]:
        # pylint: disable=too-complex
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        """
        Utility function to process the results and determine the best performing
        configs including potential repeats to help assess variability.

        Parameters
        ----------
        top_n_configs : int, optional
            How many configs to return, including the default, by default 20.
        objective_name : str, optional
            Which objective to use for sorting the configs, by default None to
            automatically select the first objective.
        method : Union[Literal["mean", "median"], float], optional
            Which statistical method to use when sorting the config groups before determining the cutoff, by default "mean".
            If a float is used, the value is expected to be between 0 and 1 and will be used as a percentile cutoff.

        Returns
        -------
        (top_n_config_results_df, top_n_config_ids, opt_target, opt_direction) : Tuple[pandas.DataFrame, List[int], str, str]
            The filtered results dataframe, the optimization target, and the optimization direction.
        """
        # Do some input checking first.
        if isinstance(method, float):
            if 0 < method or method > 1:
                raise ValueError(f"Invalid method quantile range: {method}")
        elif isinstance(method, str):
            if method not in ("mean", "median"):
                raise ValueError(f"Invalid method: {method}")
        else:
            raise ValueError(f"Invalid method type {type(method)} for method {method}")

        if objective_name is None:
            (opt_target, opt_direction) = next(iter(self.objectives.items()))
        else:
            (opt_target, opt_direction) = (objective_name, self.objectives[objective_name])
        if opt_direction not in ("min", "max"):
            raise ValueError(f"Unexpected optimization direction for target {opt_target}: {opt_direction}")

        opt_target_col = self.RESULT_COLUMN_PREFIX + opt_target
        config_id_col = "tunable_config_id"
        group_id_col = "tunable_config_trial_group_id"     # first trial_id per config group

        # Start by filtering out some outliers.
        results_df = self.results_df

        default_config_id = self.default_tunable_config_id
        assert default_config_id is not None, "Failed to determine default config id."

        # Filter out configs whose variance is too large.
        # But also make sure the default configs is still in the resulting dataframe
        # (for comparison purposes).

        non_default_config_groups_perf = results_df.loc[
            (results_df[config_id_col] != default_config_id)
        ].groupby(config_id_col)[opt_target_col]
        if len(non_default_config_groups_perf) == 0:
            raise ValueError(f"Not enough data: {len(non_default_config_groups_perf)}")

        non_default_config_groups_perf_zscores = zscore(non_default_config_groups_perf.var())
        filtered_config_results_df = results_df.loc[((results_df[config_id_col] == default_config_id) | (
            results_df[config_id_col].isin(
                non_default_config_groups_perf_zscores[non_default_config_groups_perf_zscores < 2].index
            ))
        )].reset_index()
        print(filtered_config_results_df[config_id_col].unique())

        # Also, filter results that are worse than the default.

        default_config_results_df = results_df.loc[results_df[config_id_col] == default_config_id]
        if method == "mean":
            default_val = default_config_results_df[opt_target_col].mean(numeric_only=True)
        elif method == "median":
            default_val = default_config_results_df[opt_target_col].median(numeric_only=True)
        elif isinstance(method, float) and 0 < method <= 1:
            default_val = default_config_results_df[opt_target_col].quantile(method)
        print(default_val)

        filtered_groups_perf = filtered_config_results_df.groupby(config_id_col)[opt_target_col]
        print(filtered_groups_perf.mean())
        if opt_direction == "min":
            filtered_config_results_df = filtered_config_results_df.loc[(filtered_groups_perf.mean() <= default_val)]
        elif opt_direction == "max":
            filtered_config_results_df = filtered_config_results_df.loc[(filtered_groups_perf.mean() >= default_val)]

        # Now regroup and filter to the top-N.
        grouped = results_df.groupby(config_id_col)
        if method == "mean":
            intermediate = grouped.mean(numeric_only=True)
        elif method == "median":
            intermediate = grouped.median(numeric_only=True)
        elif isinstance(method, float) and 0 < method <= 1:
            intermediate = grouped.quantile(method, numeric_only=True)
        top_n_config_ids: List[int] = intermediate.sort_values(
            by=opt_target_col, ascending=opt_direction == "min").head(top_n_configs).index.tolist()

        # Remove the default config if it's included. We'll add it back later.
        if default_config_id in top_n_config_ids:
            top_n_config_ids.remove(default_config_id)
        # Get just the top-n config reults.
        # Sort by the group ids.
        top_n_config_results_df = filtered_config_results_df[(
            filtered_config_results_df[config_id_col].isin(top_n_config_ids)
        )].sort_values([group_id_col, config_id_col])
        print(top_n_config_results_df[config_id_col].unique())
        # Place the default config at the top of the list.
        top_n_config_ids.insert(0, default_config_id)
        print(default_config_results_df[config_id_col].unique())
        top_n_config_results_df = pandas.concat([default_config_results_df, top_n_config_results_df], axis=0)
        return (top_n_config_results_df, top_n_config_ids, opt_target, opt_direction)

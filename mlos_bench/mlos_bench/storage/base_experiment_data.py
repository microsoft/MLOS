#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Base interface for accessing the stored benchmark experiment data.
"""

from abc import ABCMeta, abstractmethod
from distutils.util import strtobool    # pylint: disable=deprecated-module
from typing import Dict, List, Literal, Optional, Tuple, Union, TYPE_CHECKING

import pandas
from scipy.stats import zscore

from mlos_bench.storage.base_tunable_config_data import TunableConfigData

if TYPE_CHECKING:
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

#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Base interface for accessing the stored benchmark experiment data.

An experiment is a collection of trials that are run with a given set of scripts and
target system.

Each trial is associated with a configuration (e.g., set of tunable parameters), but
multiple trials may use the same config (e.g., for repeat run variability analysis).

See Also
--------
mlos_bench.storage :
    The base storage module for mlos_bench, which includes some basic examples
    in the documentation.
ExperimentData.results_df :
    Retrieves a pandas DataFrame of the Experiment's trials' results data.
ExperimentData.trials :
    Retrieves a dictionary of the Experiment's trials' data.
ExperimentData.tunable_configs :
    Retrieves a dictionary of the Experiment's sampled configs data.
ExperimentData.tunable_config_trial_groups :
    Retrieves a dictionary of the Experiment's trials' data, grouped by shared
    tunable config.
mlos_bench.storage.base_trial_data.TrialData :
    Base interface for accessing the stored benchmark trial data.
"""

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Literal

import pandas

from mlos_bench.storage.base_tunable_config_data import TunableConfigData
from mlos_bench.util import strtobool

if TYPE_CHECKING:
    from mlos_bench.storage.base_trial_data import TrialData
    from mlos_bench.storage.base_tunable_config_trial_group_data import (
        TunableConfigTrialGroupData,
    )


class ExperimentData(metaclass=ABCMeta):
    """
    Base interface for accessing the stored experiment benchmark data.

    An experiment groups together a set of trials that are run with a given set of
    scripts and mlos_bench configuration files.
    """

    RESULT_COLUMN_PREFIX = "result."
    """
    Prefix given to columns in :py:attr:`.ExperimentData.results_df` that contain trial
    results metrics.

    For example, if the result metric is "time", the column name will be "result.time".
    """

    CONFIG_COLUMN_PREFIX = "config."
    """
    Prefix given to columns in :py:attr:`.ExperimentData.results_df` that contain trial
    config parameters.

    For example, if the config parameter name is "param1", the column name will be
    "config.param1".
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        *,
        experiment_id: str,
        description: str,
        root_env_config: str,
        git_repo: str,
        git_commit: str,
    ):
        self._experiment_id = experiment_id
        self._description = description
        self._root_env_config = root_env_config
        self._git_repo = git_repo
        self._git_commit = git_commit

    @property
    def experiment_id(self) -> str:
        """ID of the experiment."""
        return self._experiment_id

    @property
    def description(self) -> str:
        """Description of the experiment."""
        return self._description

    @property
    def root_env_config(self) -> tuple[str, str, str]:
        """
        Root environment configuration.

        Returns
        -------
        (root_env_config, git_repo, git_commit) : tuple[str, str, str]
            A tuple of (root_env_config, git_repo, git_commit) for the root environment.
        """
        return (self._root_env_config, self._git_repo, self._git_commit)

    def __repr__(self) -> str:
        return f"Experiment :: {self._experiment_id}: '{self._description}'"

    @property
    @abstractmethod
    def objectives(self) -> dict[str, Literal["min", "max"]]:
        """
        Retrieve the experiment's objectives data from the storage.

        Returns
        -------
        objectives : dict[str, Literal["min", "max"]]
            A dictionary of the experiment's objective names (optimization_targets)
            and their directions (e.g., min or max).
        """

    @property
    @abstractmethod
    def trials(self) -> dict[int, "TrialData"]:
        """
        Retrieve the experiment's trials' data from the storage.

        Returns
        -------
        trials : dict[int, TrialData]
            A dictionary of the trials' data, keyed by trial id.
        """

    @property
    @abstractmethod
    def tunable_configs(self) -> dict[int, TunableConfigData]:
        """
        Retrieve the experiment's (tunable) configs' data from the storage.

        Returns
        -------
        trials : dict[int, TunableConfigData]
            A dictionary of the configs' data, keyed by (tunable) config id.
        """

    @property
    @abstractmethod
    def tunable_config_trial_groups(self) -> dict[int, "TunableConfigTrialGroupData"]:
        """
        Retrieve the Experiment's (Tunable) Config Trial Group data from the storage.

        Returns
        -------
        trials : dict[int, TunableConfigTrialGroupData]
            A dictionary of the trials' data, keyed by (tunable) by config id.
        """

    @property
    def default_tunable_config_id(self) -> int | None:
        """
        Retrieves the (tunable) config id for the default tunable values for this
        experiment.

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
        for _trial_id, trial in trials_items:
            # Take the first config id marked as "defaults" when it was instantiated.
            if strtobool(str(trial.metadata_dict.get("is_defaults", False))):
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
            Has columns
            [trial_id, tunable_config_id, tunable_config_trial_group_id, ts_start, ts_end, status]
            followed by tunable config parameters (prefixed with "config.") and
            trial results (prefixed with "result."). The latter can be NULLs if the
            trial was not successful.

        See Also
        --------
        :py:attr:`.ExperimentData.CONFIG_COLUMN_PREFIX`
        :py:attr:`.ExperimentData.RESULT_COLUMN_PREFIX`
        """

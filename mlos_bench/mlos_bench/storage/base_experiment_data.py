#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Base interface for accessing the stored benchmark experiment data."""

from abc import ABCMeta, abstractmethod
from distutils.util import strtobool  # pylint: disable=deprecated-module
from typing import TYPE_CHECKING, Dict, Literal, Optional, Tuple

import pandas

from mlos_bench.storage.base_tunable_config_data import TunableConfigData

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
    CONFIG_COLUMN_PREFIX = "config."

    def __init__(
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
        """

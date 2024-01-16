#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Base interface for accessing the stored benchmark data.
"""

from abc import ABCMeta, abstractmethod
from typing import Dict, Tuple

import pandas

from mlos_bench.storage.base_trial_data import TrialData


class ExperimentData(metaclass=ABCMeta):
    """
    Base interface for accessing the stored benchmark data.
    """

    RESULT_COLUMN_PREFIX = "result."
    CONFIG_COLUMN_PREFIX = "config."

    def __init__(self, *, exp_id: str, description: str,
                 root_env_config: str, git_repo: str, git_commit: str):
        self._exp_id = exp_id
        self._description = description
        self._root_env_config = root_env_config
        self._git_repo = git_repo
        self._git_commit = git_commit

    @property
    def exp_id(self) -> str:
        """
        ID of the current experiment.
        """
        return self._exp_id

    @property
    def description(self) -> str:
        """
        Description of the current experiment.
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
        return f"Experiment :: {self._exp_id}: '{self._description}'"

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
    def trials(self) -> Dict[int, TrialData]:
        """
        Retrieve the trials' data from the storage.

        Returns
        -------
        trials : Dict[int, TrialData]
            A dictionary of the trials' data, keyed by trial id.
        """

    @property
    @abstractmethod
    def results(self) -> pandas.DataFrame:
        """
        Retrieve all experimental results as a single DataFrame.

        Returns
        -------
        results : pandas.DataFrame
            A DataFrame with configurations and results from all trials of the experiment.
            Has columns [trial_id, config_id, ts_start, ts_end, status]
            followed by tunable config parameters and trial results. The latter can be NULLs
            if the trial was not successful.
        """

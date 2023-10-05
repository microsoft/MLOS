#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Base interface for accessing the stored benchmark data.
"""

from abc import ABCMeta, abstractmethod
from typing import Dict

import pandas

from mlos_bench.storage.base_trial_data import TrialData


class ExperimentData(metaclass=ABCMeta):
    """
    Base interface for accessing the stored benchmark data.
    """

    def __init__(self, exp_id: str):
        self._exp_id = exp_id

    @property
    def exp_id(self) -> str:
        """
        ID of the current experiment.
        """
        return self._exp_id

    def __repr__(self) -> str:
        return f"Experiment :: {self._exp_id}"

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
            followed by config parameters and trial results. The latter can be NULLs
            if the trial was not successful.
        """

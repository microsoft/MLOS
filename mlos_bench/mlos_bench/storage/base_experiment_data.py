#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Base interface for accessing the stored benchmark data.
"""

from abc import ABCMeta, abstractmethod
from typing import Dict

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

    @property
    @abstractmethod
    def trials(self) -> Dict[int, TrialData]:
        """
        Retrieve the trials' data from the storage.
        """

#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Base interface for accessing the stored benchmark config trial group data."""

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, Optional

import pandas

from mlos_bench.storage.base_tunable_config_data import TunableConfigData

if TYPE_CHECKING:
    from mlos_bench.storage.base_trial_data import TrialData


class TunableConfigTrialGroupData(metaclass=ABCMeta):
    """
    Base interface for accessing the stored experiment benchmark tunable config trial
    group data.

    A (tunable) config is used to define an instance of values for a set of tunable
    parameters for a given experiment and can be used by one or more trial instances
    (e.g., for repeats), which we call a (tunable) config trial group.
    """

    def __init__(
        self,
        *,
        experiment_id: str,
        tunable_config_id: int,
        tunable_config_trial_group_id: Optional[int] = None,
    ):
        self._experiment_id = experiment_id
        self._tunable_config_id = tunable_config_id
        # can be lazily initialized as necessary:
        self._tunable_config_trial_group_id: Optional[int] = tunable_config_trial_group_id

    @property
    def experiment_id(self) -> str:
        """ID of the experiment."""
        return self._experiment_id

    @property
    def tunable_config_id(self) -> int:
        """ID of the config."""
        return self._tunable_config_id

    @abstractmethod
    def _get_tunable_config_trial_group_id(self) -> int:
        """Retrieve the trial's config_trial_group_id from the storage."""
        raise NotImplementedError("subclass must implement")

    @property
    def tunable_config_trial_group_id(self) -> int:
        """
        The unique ID (within this experiment) of the (tunable) config trial group.

        This is a unique identifier for all trials in this experiment using the given
        config_id, and typically defined as the the minimum trial_id for the given
        config_id.
        """
        if self._tunable_config_trial_group_id is None:
            self._tunable_config_trial_group_id = self._get_tunable_config_trial_group_id()
        assert self._tunable_config_trial_group_id is not None
        return self._tunable_config_trial_group_id

    def __repr__(self) -> str:
        return f"TunableConfigTrialGroup :: {self._experiment_id} cid:{self.tunable_config_id}"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return (
            self._tunable_config_id == other._tunable_config_id
            and self._experiment_id == other._experiment_id
        )

    @property
    @abstractmethod
    def tunable_config(self) -> TunableConfigData:
        """
        Retrieve the (tunable) config data for this (tunable) config trial group from
        the storage.

        Returns
        -------
        TunableConfigData
        """

    @property
    @abstractmethod
    def trials(self) -> Dict[int, "TrialData"]:
        """
        Retrieve the trials' data for this (tunable) config trial group from the
        storage.

        Returns
        -------
        trials : Dict[int, TrialData]
            A dictionary of the trials' data, keyed by trial id.
        """

    @property
    @abstractmethod
    def results_df(self) -> pandas.DataFrame:
        """
        Retrieve all results for this (tunable) config trial group as a single
        DataFrame.

        Returns
        -------
        results : pandas.DataFrame
            A DataFrame with configurations and results from all trials of the experiment.
            Has columns [trial_id, config_id, ts_start, ts_end, status]
            followed by tunable config parameters (prefixed with "config.") and
            trial results (prefixed with "result."). The latter can be NULLs if the
            trial was not successful.

        See Also
        --------
        ExperimentData.results
        """

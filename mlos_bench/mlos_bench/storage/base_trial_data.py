#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Base interface for accessing the stored benchmark trial data."""
from abc import ABCMeta, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional

import pandas
from pytz import UTC

from mlos_bench.environments.status import Status
from mlos_bench.storage.base_tunable_config_data import TunableConfigData
from mlos_bench.storage.util import kv_df_to_dict
from mlos_bench.tunables.tunable import TunableValue

if TYPE_CHECKING:
    from mlos_bench.storage.base_tunable_config_trial_group_data import (
        TunableConfigTrialGroupData,
    )


class TrialData(metaclass=ABCMeta):
    """
    Base interface for accessing the stored experiment benchmark trial data.

    A trial is a single run of an experiment with a given configuration (e.g., set of
    tunable parameters).
    """

    def __init__(
        self,
        *,
        experiment_id: str,
        trial_id: int,
        tunable_config_id: int,
        ts_start: datetime,
        ts_end: Optional[datetime],
        status: Status,
    ):
        self._experiment_id = experiment_id
        self._trial_id = trial_id
        self._tunable_config_id = tunable_config_id
        assert ts_start.tzinfo == UTC, "ts_start must be in UTC"
        assert ts_end is None or ts_end.tzinfo == UTC, "ts_end must be in UTC if not None"
        self._ts_start = ts_start
        self._ts_end = ts_end
        self._status = status

    def __repr__(self) -> str:
        return (
            f"Trial :: {self._experiment_id}:{self._trial_id} "
            f"cid:{self._tunable_config_id} {self._status.name}"
        )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self._experiment_id == other._experiment_id and self._trial_id == other._trial_id

    @property
    def experiment_id(self) -> str:
        """ID of the experiment this trial belongs to."""
        return self._experiment_id

    @property
    def trial_id(self) -> int:
        """ID of the trial."""
        return self._trial_id

    @property
    def ts_start(self) -> datetime:
        """Start timestamp of the trial (UTC)."""
        return self._ts_start

    @property
    def ts_end(self) -> Optional[datetime]:
        """End timestamp of the trial (UTC)."""
        return self._ts_end

    @property
    def status(self) -> Status:
        """Status of the trial."""
        return self._status

    @property
    def tunable_config_id(self) -> int:
        """ID of the (tunable) configuration of the trial."""
        return self._tunable_config_id

    @property
    @abstractmethod
    def tunable_config(self) -> TunableConfigData:
        """
        Retrieve the trials' tunable configuration data from the storage.

        Note: this corresponds to the Trial object's "tunables" property.

        Returns
        -------
        tunable_config : TunableConfigData
            A TunableConfigData object.
        """

    @property
    @abstractmethod
    def tunable_config_trial_group(self) -> "TunableConfigTrialGroupData":
        """Retrieve the trial's (tunable) config trial group data from the storage."""

    @property
    @abstractmethod
    def results_df(self) -> pandas.DataFrame:
        """
        Retrieve the trials' results from the storage.

        Returns
        -------
        results : pandas.DataFrame
            A dataframe with the trial results.
            It has two `str` columns, "metric" and "value".
            If the trial status is not SUCCEEDED, the dataframe is empty.
        """

    @property
    def results_dict(self) -> Dict[str, Optional[TunableValue]]:
        """
        Retrieve the trials' results from the storage as a dict.

        Returns
        -------
        results : dict
        """
        return kv_df_to_dict(self.results_df)

    @property
    @abstractmethod
    def telemetry_df(self) -> pandas.DataFrame:
        """
        Retrieve the trials' telemetry from the storage as a dataframe.

        Returns
        -------
        config : pandas.DataFrame
            A dataframe with the trial telemetry, if there is any.
            It has one `datetime` column, "ts", and two `str` columns, "metric" and "value".
            If the trial status is not SUCCEEDED, or there is no telemetry data,
            the dataframe is empty.
        """

    @property
    @abstractmethod
    def metadata_df(self) -> pandas.DataFrame:
        """
        Retrieve the trials' metadata parameters as a dataframe.

        Note: this corresponds to the Trial object's "config" property.

        Returns
        -------
        metadata : pandas.DataFrame
            An optional dataframe with the metadata associated with the trial.
            It has two `str` columns, "parameter" and "value".
            Returns an empty dataframe if there is no metadata.
        """

    @property
    def metadata_dict(self) -> dict:
        """
        Retrieve the trials' metadata parameters as a dict.

        Note: this corresponds to the Trial object's "config" property.

        Returns
        -------
        metadata : dict
        """
        return kv_df_to_dict(self.metadata_df)

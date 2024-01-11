#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Base interface for accessing the stored benchmark data.
"""
from abc import ABCMeta, abstractmethod
from datetime import datetime
from typing import Optional

import pandas

from mlos_bench.environments.status import Status


class TrialData(metaclass=ABCMeta):
    """
    Base interface for accessing the stored benchmark data.
    """

    def __init__(self, *,
                 exp_id: str,
                 trial_id: int,
                 config_id: int,
                 ts_start: datetime,
                 ts_end: Optional[datetime],
                 status: Status):
        self._exp_id = exp_id
        self._trial_id = trial_id
        self._config_id = config_id
        self._ts_start = ts_start
        self._ts_end = ts_end
        self._status = status

    def __repr__(self) -> str:
        return f"{self._exp_id}:{self._trial_id} config:{self._config_id} {self._status.name}"

    @property
    def exp_id(self) -> str:
        """
        ID of the experiment this trial belongs to.
        """
        return self._exp_id

    @property
    def trial_id(self) -> int:
        """
        ID of the current trial.
        """
        return self._trial_id

    @property
    def config_id(self) -> int:
        """
        ID of the configuration of the current trial.
        """
        return self._config_id

    @property
    def ts_start(self) -> datetime:
        """
        Start timestamp of the current trial (UTC).
        """
        return self._ts_start

    @property
    def ts_end(self) -> Optional[datetime]:
        """
        End timestamp of the current trial (UTC).
        """
        return self._ts_end

    @property
    def status(self) -> Status:
        """
        Status of the current trial.
        """
        return self._status

    @property
    @abstractmethod
    def tunable_config(self) -> pandas.DataFrame:
        """
        Retrieve the trials' tunable configuration from the storage.

        Note: this corresponds to the Trial object's "tunables" property.

        Returns
        -------
        config : pandas.DataFrame
            A dataframe with the tunable configuration of the current trial.
            It has two `str` columns, "parameter" and "value".
        """

    @property
    @abstractmethod
    def results(self) -> pandas.DataFrame:
        """
        Retrieve the trials' results from the storage.

        Returns
        -------
        config : pandas.DataFrame
            A dataframe with the trial results.
            It has two `str` columns, "metric" and "value".
            If the trial status is not SUCCEEDED, the dataframe is empty.
        """

    @property
    @abstractmethod
    def telemetry(self) -> pandas.DataFrame:
        """
        Retrieve the trials' telemetry from the storage.

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
    def metadata(self) -> pandas.DataFrame:
        """
        Retrieve the trials' metadata parameters.

        Note: this corresponds to the Trial object's "config" property.

        Returns
        -------
        metadata : pandas.DataFrame
            An optional dataframe with the metadata associated with the trial.
            It has two `str` columns, "parameter" and "value".
            Returns an empty dataframe if there is no metadata.
        """

#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Enum for the status of the benchmark/environment Trial or Experiment."""

import enum
import logging
from typing import Any

_LOG = logging.getLogger(__name__)


class Status(enum.Enum):
    """Enum for the status of the benchmark/environment Trial or Experiment."""

    UNKNOWN = 0
    PENDING = 1
    READY = 2
    RUNNING = 3
    SUCCEEDED = 4
    CANCELED = 5
    FAILED = 6
    TIMED_OUT = 7

    @staticmethod
    def parse(status: Any) -> "Status":
        """
        Convert the input to a Status enum.

        Parameters
        ----------
        status : Any
            The status to parse. This can be a string (or string convertible),
            int, or Status enum.

        Returns
        -------
        Status
            The corresponding Status enum value or else UNKNOWN if the input is not
            recognized.
        """
        if isinstance(status, Status):
            return status
        if not isinstance(status, str):
            _LOG.warning("Expected type %s for status: %s", type(status), status)
            status = str(status)
        if status.isdigit():
            try:
                return Status(int(status))
            except ValueError:
                _LOG.warning("Unknown status: %d", int(status))
        try:
            status = status.upper().strip()
            return Status[status]
        except KeyError:
            _LOG.warning("Unknown status: %s", status)
        return Status.UNKNOWN

    def is_good(self) -> bool:
        """Check if the status of the benchmark/environment is good."""
        return self in {
            Status.PENDING,
            Status.READY,
            Status.RUNNING,
            Status.SUCCEEDED,
        }

    # Class based accessor method to avoid circular import
    @staticmethod
    def completed_statuses() -> frozenset["Status"]:
        """Get the set of :py:data:`.COMPLETED_STATUSES`."""
        return COMPLETED_STATUSES

    def is_completed(self) -> bool:
        """Check if the status of the benchmark/environment Trial or Experiment is one
        of :py:data:`.COMPLETED_STATUSES`.
        """
        return self in COMPLETED_STATUSES

    def is_pending(self) -> bool:
        """Check if the status of the benchmark/environment Trial or Experiment is
        PENDING.
        """
        return self == Status.PENDING

    def is_ready(self) -> bool:
        """Check if the status of the benchmark/environment Trial or Experiment is
        READY.
        """
        return self == Status.READY

    def is_running(self) -> bool:
        """Check if the status of the benchmark/environment Trial or Experiment is
        RUNNING.
        """
        return self == Status.RUNNING

    def is_succeeded(self) -> bool:
        """Check if the status of the benchmark/environment Trial or Experiment is
        SUCCEEDED.
        """
        return self == Status.SUCCEEDED

    def is_failed(self) -> bool:
        """Check if the status of the benchmark/environment Trial or Experiment is
        FAILED.
        """
        return self == Status.FAILED

    def is_canceled(self) -> bool:
        """Check if the status of the benchmark/environment Trial or Experiment is
        CANCELED.
        """
        return self == Status.CANCELED

    def is_timed_out(self) -> bool:
        """Check if the status of the benchmark/environment Trial or Experiment is
        TIMED_OUT.
        """
        return self == Status.TIMED_OUT


COMPLETED_STATUSES = frozenset(
    {
        Status.SUCCEEDED,
        Status.CANCELED,
        Status.FAILED,
        Status.TIMED_OUT,
    }
)
"""
The set of completed statuses.

Includes all statuses that indicate the trial or experiment has finished, either
successfully or not.
This set is used to determine if a trial or experiment has reached a final state.
This includes:
- :py:attr:`.Status.SUCCEEDED`: The trial or experiment completed successfully.
- :py:attr:`.Status.CANCELED`: The trial or experiment was canceled.
- :py:attr:`.Status.FAILED`: The trial or experiment failed.
- :py:attr:`.Status.TIMED_OUT`: The trial or experiment timed out.
"""

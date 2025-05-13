#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Enum for the status of the benchmark/environment Trial or Experiment."""

import enum
import logging

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
    def from_str(status_str: str) -> "Status":
        """Convert a string to a Status enum."""
        if status_str.isdigit():
            try:
                return Status(int(status_str))
            except ValueError:
                _LOG.warning("Unknown status: %d", int(status_str))
        try:
            status_str = status_str.upper()
            return Status[status_str]
        except KeyError:
            _LOG.warning("Unknown status: %s", status_str)
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
    def completed_statuses() -> set["Status"]:
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


COMPLETED_STATUSES = {
    Status.SUCCEEDED,
    Status.CANCELED,
    Status.FAILED,
    Status.TIMED_OUT,
}
"""The set of completed statuses."""

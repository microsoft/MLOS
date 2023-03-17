#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Enum for the status of the benchmark/environment.
"""

import enum


class Status(enum.Enum):
    """
    Enum for the status of the benchmark/environment.
    """

    UNKNOWN = 0
    PENDING = 1
    READY = 2
    RUNNING = 3
    SUCCEEDED = 4
    CANCELED = 5
    FAILED = 6
    TIMED_OUT = 7

    @property
    def is_good(self):
        """
        Check if the status of the benchmark/environment is good.
        """
        return self in {
            Status.PENDING,
            Status.READY,
            Status.RUNNING,
            Status.SUCCEEDED,
        }

    @property
    def is_pending(self):
        """
        Check if the status of the benchmark/environment is PENDING.
        """
        return self == Status.PENDING

    @property
    def is_ready(self):
        """
        Check if the status of the benchmark/environment is READY.
        """
        return self == Status.READY

    @property
    def is_succeeded(self):
        """
        Check if the status of the benchmark/environment is SUCCEEDED.
        """
        return self == Status.SUCCEEDED

    @property
    def is_failed(self):
        """
        Check if the status of the benchmark/environment is FAILED.
        """
        return self == Status.FAILED

    @property
    def is_canceled(self):
        """
        Check if the status of the benchmark/environment is CANCELED.
        """
        return self == Status.CANCELED

    @property
    def is_timed_out(self):
        """
        Check if the status of the benchmark/environment is TIMEDOUT.
        """
        return self == Status.FAILED

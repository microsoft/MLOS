"""
Enum for the status of the benchmark.
"""

import enum


class Status(enum.Enum):
    """
    Enum for the status of the benchmark.
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
        Check if the status of the environment is good.
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
        Check if the status of the environment is PENDING.
        """
        return self == Status.PENDING

    @property
    def is_ready(self):
        """
        Check if the status of the environment is READY.
        """
        return self == Status.READY

    @property
    def is_succeeded(self):
        """
        Check if the status of the environment is SUCCEEDED.
        """
        return self == Status.SUCCEEDED

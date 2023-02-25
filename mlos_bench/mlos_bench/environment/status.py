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

    @staticmethod
    def is_good(status):
        """
        Check if the status of the environment is good.
        """
        return status in {
            Status.PENDING,
            Status.READY,
            Status.RUNNING,
            Status.SUCCEEDED,
        }

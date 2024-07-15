#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Enum for the status of the benchmark/environment."""

import enum


class Status(enum.Enum):
    """Enum for the status of the benchmark/environment."""

    UNKNOWN = 0
    PENDING = 1
    READY = 2
    RUNNING = 3
    SUCCEEDED = 4
    CANCELED = 5
    FAILED = 6
    TIMED_OUT = 7

    def is_good(self) -> bool:
        """Check if the status of the benchmark/environment is good."""
        return self in {
            Status.PENDING,
            Status.READY,
            Status.RUNNING,
            Status.SUCCEEDED,
        }

    def is_completed(self) -> bool:
        """Check if the status of the benchmark/environment is one of {SUCCEEDED,
        CANCELED, FAILED, TIMED_OUT}.
        """
        return self in {
            Status.SUCCEEDED,
            Status.CANCELED,
            Status.FAILED,
            Status.TIMED_OUT,
        }

    def is_pending(self) -> bool:
        """Check if the status of the benchmark/environment is PENDING."""
        return self == Status.PENDING

    def is_ready(self) -> bool:
        """Check if the status of the benchmark/environment is READY."""
        return self == Status.READY

    def is_succeeded(self) -> bool:
        """Check if the status of the benchmark/environment is SUCCEEDED."""
        return self == Status.SUCCEEDED

    def is_failed(self) -> bool:
        """Check if the status of the benchmark/environment is FAILED."""
        return self == Status.FAILED

    def is_canceled(self) -> bool:
        """Check if the status of the benchmark/environment is CANCELED."""
        return self == Status.CANCELED

    def is_timed_out(self) -> bool:
        """Check if the status of the benchmark/environment is TIMED_OUT."""
        return self == Status.FAILED

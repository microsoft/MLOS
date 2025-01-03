#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Mock remote services for testing purposes."""

from typing import Any

from mlos_bench.environments.status import Status


def mock_operation(*_args: Any, **_kwargs: Any) -> tuple[Status, dict]:
    """
    Mock VM operation that always succeeds.

    Returns
    -------
    result : (Status, dict)
        A pair of Status and result, always (SUCCEEDED, {}).
    """
    return Status.SUCCEEDED, {}

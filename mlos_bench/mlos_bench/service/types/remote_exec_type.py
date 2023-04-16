#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Protocol interface for Service types that provide helper functions to run
scripts on a remote host OS.
"""

from typing import List, Tuple, Protocol, runtime_checkable, TYPE_CHECKING


if TYPE_CHECKING:
    from mlos_bench.environment.status import Status


@runtime_checkable
class SupportsRemoteExec(Protocol):
    # pylint: disable=too-few-public-methods
    """
    Protocol interface for Service types that provide helper functions to run
    scripts on a remote host OS.
    """

    def remote_exec(self, script: List[str], params: dict) -> Tuple["Status", dict]:
        """
        Run a command on remote host OS.

        Parameters
        ----------
        script : List[str]
            A list of lines to execute as a script on a remote VM.
        params : dict
            Flat dictionary of (key, value) pairs of parameters.
            They usually come from `const_args` and `tunable_params`
            properties of the Environment.

        Returns
        -------
        result : (Status, dict)
            A pair of Status and result.
            Status is one of {PENDING, SUCCEEDED, FAILED}
        """

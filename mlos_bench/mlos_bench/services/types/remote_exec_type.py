#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Protocol interface for Service types that provide helper functions to run scripts on
a remote host OS.
"""

from typing import TYPE_CHECKING, Iterable, Protocol, Tuple, runtime_checkable

if TYPE_CHECKING:
    from mlos_bench.environments.status import Status


@runtime_checkable
class SupportsRemoteExec(Protocol):
    """Protocol interface for Service types that provide helper functions to run scripts
    on a remote host OS.
    """

    def remote_exec(
        self,
        script: Iterable[str],
        config: dict,
        env_params: dict,
    ) -> Tuple["Status", dict]:
        """
        Run a command on remote host OS.

        Parameters
        ----------
        script : Iterable[str]
            A list of lines to execute as a script on a remote VM.
        config : dict
            Flat dictionary of (key, value) pairs of parameters.
            They usually come from `const_args` and `tunable_params`
            properties of the Environment.
        env_params : dict
            Parameters to pass as *shell* environment variables into the script.
            This is usually a subset of `config` with some possible conversions.

        Returns
        -------
        result : (Status, dict)
            A pair of Status and result.
            Status is one of {PENDING, SUCCEEDED, FAILED}
        """

    def get_remote_exec_results(self, config: dict) -> Tuple["Status", dict]:
        """
        Get the results of the asynchronously running command.

        Parameters
        ----------
        config : dict
            Flat dictionary of (key, value) pairs of tunable parameters.
            Must have the "asyncResultsUrl" key to get the results.
            If the key is not present, return Status.PENDING.

        Returns
        -------
        result : (Status, dict)
            A pair of Status and result.
            Status is one of {PENDING, SUCCEEDED, FAILED, TIMED_OUT}
        """

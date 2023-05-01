#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
A collection Service functions for mocking remote script execution.
"""

import logging

from typing import Iterable, Tuple

from mlos_bench.environments.status import Status
from mlos_bench.services.base_service import Service
from mlos_bench.services.types.remote_exec_type import SupportsRemoteExec
from mlos_bench.util import check_required_params

_LOG = logging.getLogger(__name__)


class MockRemoteExecService(Service, SupportsRemoteExec):
    """
    Mock remote script execution service.
    """

    def __init__(self, config: dict, parent: Service):
        """
        Create a new instance of mock remote exec service.

        Parameters
        ----------
        config : dict
            Free-format dictionary that contains the benchmark environment
            configuration.
        parent : Service
            Parent service that can provide mixin functions.
        """
        super().__init__(config, parent)

        check_required_params(
            config, {
                "vmName",
            }
        )

        # Register methods that we want to expose to the Environment objects.
        self.register([
            self.remote_exec,
            self.get_remote_exec_results,
        ])

    def remote_exec(self, script: Iterable[str], params: dict) -> Tuple[Status, dict]:
        """
        Run a command on remote host OS.

        Parameters
        ----------
        script : Iterable[str]
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
        return (Status.SUCCEEDED, {})

    def get_remote_exec_results(self, params: dict) -> Tuple[Status, dict]:
        """
        Get the results of the asynchronously running command.

        Parameters
        ----------
        params : dict
            Flat dictionary of (key, value) pairs of tunable parameters.
            Must have the "asyncResultsUrl" key to get the results.
            If the key is not present, return Status.PENDING.

        Returns
        -------
        result : (Status, dict)
            A pair of Status and result.
            Status is one of {PENDING, SUCCEEDED, FAILED, TIMED_OUT}
        """
        return (Status.SUCCEEDED, {})

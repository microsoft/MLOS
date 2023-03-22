#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
An abstract interface class for the remote execution service mix-ins.
"""

import logging

from typing import Any, List, Dict, Tuple

from abc import ABCMeta, abstractmethod

from mlos_bench.environment.status import Status
from mlos_bench.service.base_service import Service

_LOG = logging.getLogger(__name__)


class RemoteExecService(Service, metaclass=ABCMeta):
    """
    An abstract interface class for the remote execution service mix-ins.
    """

    @abstractmethod
    def remote_exec(self, script: List[str], params: Dict[str, Any]) -> Tuple[Status, Dict]:
        """
        Run a command on Azure VM.

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
        raise NotImplementedError("Must be implemented by a derived class.")

    @abstractmethod
    def get_remote_exec_results(self, params: Dict) -> Tuple[Status, Dict]:
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
        raise NotImplementedError("Must be implemented by a derived class.")

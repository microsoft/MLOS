#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Service types (i.e., :py:class:`Protocol`s) for declaring implementation
:py:class:`~mlos_bench.services.base_service.Service` behavior for
:py:mod:`~mlos_bench.environments` to use in :py:mod:`mlos_bench`.

Overview
--------
Service loading in ``mlos_bench`` uses a
[mix-in](https://en.wikipedia.org/wiki/Mixin#In_Python) approach to combine the
functionality of multiple classes specified at runtime through config files into
a single class that the :py:mod:`~mlos_bench.environments` can use to invoke the
actions that they were configured to perform (e.g., provisioning a VM, deploying
a network, running a script, etc.).

Since Services are loaded at runtime and can be swapped out by referencing a
different set of ``--services`` config files via the :py:mod:`mlos_bench.run`
CLI option, this can make it difficult to do type and config checking.

To address this we define ``@runtime_checkable`` decorated
[`Protocols`](https://peps.python.org/pep-0544/) ("interfaces" in other
languages) to declare the expected behavior of the ``Services`` that are loaded
at runtime in the ``Environments`` that use them.

For example, the :py:class:`.SupportsFileShareOps` Protocol declares the
expected behavior of a Service that can
:py:meth:`~.SupportsFileShareOps.download` and
:py:meth:`~.SupportsFileShareOps.upload` files to and from a remote file share.

But we can have more than one Service that implements that Protocol (e.g., one
for Azure, one for AWS, one for a remote SSH server, etc.).

This allows us to define the expected behavior of the Service that the
Environment will need, but not the specific implementation details.

It also allows users to define Environment configs that are more reusable so
that we can swap out the Service implementations at runtime without having to
change the Environment config.

That way we can run Experiments on more than one platform rather easily.

See the classes below for an overview of the types of Services that are
currently available for Environments.

Notes
-----
If you find that there are missing types or that you need to add a new Service
type, please `submit a PR <https://github.com/microsoft/MLOS>`_ to add it here.
"""

from mlos_bench.services.types.authenticator_type import SupportsAuth
from mlos_bench.services.types.config_loader_type import SupportsConfigLoading
from mlos_bench.services.types.fileshare_type import SupportsFileShareOps
from mlos_bench.services.types.host_provisioner_type import SupportsHostProvisioning
from mlos_bench.services.types.local_exec_type import SupportsLocalExec
from mlos_bench.services.types.network_provisioner_type import (
    SupportsNetworkProvisioning,
)
from mlos_bench.services.types.remote_config_type import SupportsRemoteConfig
from mlos_bench.services.types.remote_exec_type import SupportsRemoteExec

__all__ = [
    "SupportsAuth",
    "SupportsConfigLoading",
    "SupportsFileShareOps",
    "SupportsHostProvisioning",
    "SupportsLocalExec",
    "SupportsNetworkProvisioning",
    "SupportsRemoteConfig",
    "SupportsRemoteExec",
]

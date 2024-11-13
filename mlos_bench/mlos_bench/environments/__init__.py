#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Tunable Environments for mlos_bench.

Environments are classes that represent an execution setting (environment) for
running a benchmark or tuning process.

An Environment goes through a series of phases (e.g.,
:py:meth:`~.Environment.setup`, :py:meth:`~.Environment.run`,
:py:meth:`~.Environment.teardown`) that can be used to prepare a VM, workload, etc.;
run a benchmark, script, etc.; and clean up afterwards.

They can be stacked together with the :py:class:`.CompositeEnv` class to
represent complex setups (e.g., an appication running on a VM).

Each environment can use
:py:class:`~mlos_bench.tunables.tunable_groups.TunableGroups` to specify the set of
configuration parameters that can be optimized or searched.
At each iteration of the optimization process, the optimizer will generate a set of
values for the `Tunables` that the environment can use to configure itself.

Environments can also reference :py:mod:`~mlos_bench.services` that provide the
necessary support to enact the actions that environment needs for each of its
phases depending upon where its being deployed (e.g., local machine, remote machine,
cloud provider VM, etc.)

See below for the set of Environments currently available in this package.
Note that additional ones can also be created by extending the base
:py:class:`.Environment` class.

Examples
--------
While this documentation is generated from the source code and is intended to be a
useful reference on the internal details, most users will be more interested in
generating json configs to be used with the ``mlos_bench`` command line tool.

TODO: Add examples here.

See Also
--------
`mlos_bench/environments/README.md
<https://github.com/microsoft/MLOS/tree/main/mlos_bench/mlos_bench/environments/>`_
for additional documentation in the source tree.

`mlos_bench/config/environments/README.md
<https://github.com/microsoft/MLOS/tree/main/mlos_bench/mlos_bench/config/environments/>`_
for additional config examples in the source tree.
"""

from mlos_bench.environments.base_environment import Environment
from mlos_bench.environments.composite_env import CompositeEnv
from mlos_bench.environments.local.local_env import LocalEnv
from mlos_bench.environments.local.local_fileshare_env import LocalFileShareEnv
from mlos_bench.environments.mock_env import MockEnv
from mlos_bench.environments.remote.remote_env import RemoteEnv
from mlos_bench.environments.status import Status

__all__ = [
    "Status",
    "Environment",
    "MockEnv",
    "RemoteEnv",
    "LocalEnv",
    "LocalFileShareEnv",
    "CompositeEnv",
]

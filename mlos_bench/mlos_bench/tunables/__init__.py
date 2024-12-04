#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Tunables classes for Environments in mlos_bench.

TODO: Add more documentation and examples here.


Examples
--------
>>> from mlos_bench.tunables import TunableGroups
>>> from mlos_bench.services.config_persistence import ConfigPersistenceService
>>> service = ConfigPersistenceService()
>>> tunables = service.load_tunables(jsons=['{"tunable_group_name": {"cost": 1, "params": {"param1": {"type": "categorical", "values": ["red", "blue", "green"], "default": "green"}}}}'], parent=TunableGroups())
>>> tunables
{ tunable_group_name::param1[categorical](['red', 'blue', 'green']:green)=green }
"""

from mlos_bench.tunables.tunable import Tunable, TunableValue
from mlos_bench.tunables.tunable_groups import TunableGroups

__all__ = [
    "Tunable",
    "TunableValue",
    "TunableGroups",
]

#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Hashable dictionary implementation.
"""

from typing import Dict

from mlos_bench.tunables.tunable import TunableValue


class HashableDict(Dict[str, TunableValue]):
    """
    Simple hashable dict implementation.
    """

    def __hash__(self) -> int:  # type: ignore[override]
        # Note: this may not work
        return hash(tuple(sorted(self.items())))

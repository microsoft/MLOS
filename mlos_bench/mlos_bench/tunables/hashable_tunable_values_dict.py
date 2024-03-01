#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Hashable dictionary implementation.
"""

from typing import Any, Dict

from mlos_bench.tunables.tunable import TunableValue, TunableValueTypeTuple


class HashableTunableValuesDict(Dict[str, TunableValue]):
    """
    Simple hashable dict implementation of tunable values.

    Subtype of Dict[str, TunableValue] that is hashable so that it can be stored in
    sets.

    Note: these configs are expected to be immutable.
    """

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._check_types()

    def _check_types(self) -> None:
        key_types = {str(key): type(key) for key in self.keys()}
        val_types = {str(val): type(val) for val in self.values()}
        assert all(key_type in [str] for key_type in key_types.values()), \
            f"Invalid tunable values dict keys types for {self}: {key_types}"
        assert all(val_type in TunableValueTypeTuple for val_type in val_types.values()), \
            f"Invalid tunable values dict value types for {self}: {val_types}"

    def __delitem__(self, __key: str) -> None:
        raise NotImplementedError("HashableTunableValuesDict is immutable")

    def __setitem__(self, __key: str, __value: int | float | str | None) -> None:
        raise NotImplementedError("HashableTunableValuesDict is immutable")

    def __hash__(self) -> int:  # type: ignore[override]
        # Note: this doesn't work for nested dicts, but we don't need that for now.
        return hash(tuple(sorted(self.items())))

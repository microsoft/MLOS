#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for checking tunable size properties.
"""

import pytest

from mlos_bench.tunables.hashable_tunable_values_dict import HashableTunableValuesDict


def test_invalid_hashable_tunable_values_dict() -> None:
    """
    Test invalid hashable tunable values dict.
    """
    with pytest.raises(AssertionError):
        HashableTunableValuesDict({"a": 1, 2: "bad key"})
    with pytest.raises(AssertionError):
        HashableTunableValuesDict({"a": ["invalid", "value"], "b": 2})


def test_hashable_tunable_values_dict() -> None:
    """
    Test hashable tunable values dict.
    """
    source = {"a": 1, "b": 2, "c": 3}
    alt = source.copy()
    alt["c"] = alt["c"] + 1

    hashable_source = HashableTunableValuesDict(source)
    hashable_alt = HashableTunableValuesDict(alt)

    with pytest.raises(NotImplementedError):
        hashable_source["a"] = 2

    with pytest.raises(NotImplementedError):
        del hashable_source["a"]

    assert hash(hashable_source) == hash(HashableTunableValuesDict(source))
    assert hash(hashable_source) != hash(hashable_alt)

    configs_set = set({hashable_source, hashable_alt})
    assert hashable_source in configs_set
    assert hashable_alt in configs_set

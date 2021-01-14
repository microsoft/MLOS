#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import pytest
from mlos.Utils.KeyOrderedDict import KeyOrderedDict

class TestKeyOrderedDict:

    def test_sanity(self):
        keys = [letter for letter in "abcdefghijklmnopqrstuvwxyz"]
        values = [letter.upper() for letter in keys]

        key_ordered_dict = KeyOrderedDict(ordered_keys=keys, value_type=str)
        for key, value in zip(keys, values):
            key_ordered_dict[key] = value

        for i, (key, value) in enumerate(key_ordered_dict):
            assert key == keys[i]
            assert value == values[i]

        key_ordered_dict['a'] = None
        assert key_ordered_dict[0] is None
        assert key_ordered_dict['a'] is None

        with pytest.raises(TypeError):
            key_ordered_dict['b'] = 1

        assert key_ordered_dict[1] == "B"
        assert key_ordered_dict['b'] == "B"
        key_ordered_dict['b'] = "1"
        assert key_ordered_dict[1] == "1"
        assert key_ordered_dict['b'] == "1"

        with pytest.raises(KeyError):
            _ = key_ordered_dict['A']

        with pytest.raises(IndexError):
            _ = key_ordered_dict[100]

        assert len(keys) == len(key_ordered_dict)

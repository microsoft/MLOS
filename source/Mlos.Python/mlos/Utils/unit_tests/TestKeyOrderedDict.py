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

        

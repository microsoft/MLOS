#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from typing import Dict, Iterator, List, Tuple, Union

class KeyOrderedDict:
    """Dictionary where entries can be enumerated and accessed in pre-specified order.

    """

    def __init__(self, ordered_keys: List[str], value_type: type, dictionary: Dict[str, object] = None):
        assert all(isinstance(key, str) for key in ordered_keys)
        self.value_type = value_type
        self._ordered_keys = ordered_keys
        self._dict = {key: None for key in self._ordered_keys}

        if dictionary is None:
            dictionary = {}

        for key in self._ordered_keys:
            if key in dictionary:
                value = dictionary[key]
                assert isinstance(value, (self.value_type, None))
                self._dict[key] = value
            else:
                self._dict[key] = None

    def __getitem__(self, key_or_index: Union[str, int]) -> object:
        key = self._to_key(key_or_index)
        return self._dict[key]

    def __setitem__(self, key_or_index: Union[str, int], value) -> None:
        assert isinstance(value, (self.value_type, None))
        key = self._to_key(key_or_index)
        self._dict[key] = value

    def __iter__(self) -> Iterator[Tuple[str, object]]:
        for key in self._ordered_keys:
            yield key, self._dict[key]

    def _to_key(self, key_or_index: Union[str, int]) -> str:
        if isinstance(key_or_index, str):
            return key_or_index
        if isinstance(key_or_index, int):
            return self._ordered_keys[key_or_index]
        raise ValueError(f"{key_or_index} is neither an int nor a str.")

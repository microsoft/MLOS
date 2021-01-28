#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import json
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
                assert isinstance(value, self.value_type) or value is None
                self._dict[key] = value
            else:
                self._dict[key] = None

    @property
    def ordered_keys(self):
        return [key for key in self._ordered_keys]

    def __getitem__(self, key_or_index: Union[str, int]) -> object:
        key = self._to_key(key_or_index)
        return self._dict[key]

    def __setitem__(self, key_or_index: Union[str, int], value) -> None:
        if not (isinstance(value, self.value_type) or value is None):
            raise TypeError(f'Value must be of type {str(self.value_type)} not {type(value)}')
        key = self._to_key(key_or_index)
        self._dict[key] = value

    def __iter__(self) -> Iterator[Tuple[str, object]]:
        for key in self._ordered_keys:
            yield key, self._dict[key]

    def __len__(self):
        return len(self._ordered_keys)

    def _to_key(self, key_or_index: Union[str, int]) -> str:
        if isinstance(key_or_index, str):
            return key_or_index
        if isinstance(key_or_index, int):
            return self._ordered_keys[key_or_index]
        raise ValueError(f"{key_or_index} is neither an int nor a str.")

    def to_json(self):
        return json.dumps({key: value.to_json() for key, value in self})

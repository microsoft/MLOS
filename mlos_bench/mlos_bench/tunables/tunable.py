#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tunable parameter definition.
"""
import copy
import collections

from typing import Any, List, Tuple


class Tunable:  # pylint: disable=too-many-instance-attributes
    """
    A tunable parameter definition and its current value.
    """

    _TYPE = {
        "int": int,
        "float": float,
        "categorical": str,
    }

    def __init__(self, name: str, config: dict):
        """
        Create an instance of a new tunable parameter.

        Parameters
        ----------
        name : str
            Human-readable identifier of the tunable parameter.
        config : dict
            Python dict that represents a Tunable (e.g., deserialized from JSON)
        """
        self._name = name
        self._type = config["type"]  # required
        self._description = config.get("description")
        self._default = config.get("default")
        self._values = config.get("values")
        self._range = config.get("range")
        self._special = config.get("special")
        self._current_value = self._default
        if self._type == "categorical":
            if not (self._values and isinstance(self._values, collections.abc.Iterable)):
                raise ValueError("Must specify values for the categorical type")
            if self._range is not None:
                raise ValueError("Range must be None for the categorical type")
            if self._special is not None:
                raise ValueError("Special values must be None for the categorical type")
        elif self._type in {"int", "float"}:
            if not self._range or len(self._range) != 2 or self._range[0] >= self._range[1]:
                raise ValueError(f"Invalid range: {self._range}")
        else:
            raise ValueError(f"Invalid parameter type: {self._type}")

    def __repr__(self) -> str:
        """
        Produce a human-readable version of the Tunable (mostly for logging).

        Returns
        -------
        string : str
            A human-readable version of the Tunable.
        """
        return f"{self._name}={self._current_value}"

    def __eq__(self, other) -> bool:
        """
        Check if two Tunable objects are equal.

        Parameters
        ----------
        other : Tunable
            A tunable object to compare to.

        Returns
        -------
        is_equal : bool
            True if the Tunables correspond to the same parameter and have the same value and type.
            NOTE: ranges and special values are not currently considered in the comparison.
        """
        return (
            self._name == other._name and
            self._type == other._type and
            self._current_value == other._current_value
        )

    def copy(self):
        """
        Deep copy of the Tunable object.

        Returns
        -------
        tunable : Tunable
            A new Tunable object that is a deep copy of the original one.
        """
        return copy.deepcopy(self)

    @property
    def value(self):
        """
        Get the current value of the tunable.
        """
        return self._current_value

    @value.setter
    def value(self, value):
        """
        Set the current value of the tunable.
        """
        # We need this coercion for the values produced by some optimizers
        # (e.g., scikit-optimize) and for data restored from certain storage
        # systems (where values can be strings).
        coerced_value = self._TYPE[self._type](value)
        if not self.is_valid(coerced_value):
            raise ValueError(f"Invalid value for the tunable: {value}")
        self._current_value = coerced_value
        return self._current_value

    def is_valid(self, value) -> bool:
        """
        Check if the value can be assigned to the tunable.

        Parameters
        ----------
        value : Any
            Value to validate.

        Returns
        -------
        is_valid : bool
            True if the value is valid, False otherwise.
        """
        if self._type == "categorical":
            return value in self._values
        elif self._type in {"int", "float"} and self._range:
            return (self._range[0] <= value <= self._range[1]) or value == self._default
        else:
            raise ValueError(f"Invalid parameter type: {self._type}")

    @property
    def name(self) -> str:
        """
        Get the name / string ID of the tunable.
        """
        return self._name

    @property
    def type(self) -> str:
        """
        Get the data type of the tunable.

        Returns
        -------
        type : str
            Data type of the tunable - one of {'int', 'float', 'categorical'}.
        """
        return self._type

    @property
    def range(self) -> Tuple[Any, Any]:
        """
        Get the range of the tunable if it is numerical, None otherwise.

        Returns
        -------
        range : (number, number)
            A 2-tuple of numbers that represents the range of the tunable.
            Numbers can be int or float, depending on the type of the tunable.
        """
        return self._range

    @property
    def categorical_values(self) -> List[str]:
        """
        Get the list of all possible values of a categorical tunable.
        Return None if the tunable is not categorical.

        Returns
        -------
        values : List[str]
            List of all possible values of a categorical tunable.
        """
        return self._values

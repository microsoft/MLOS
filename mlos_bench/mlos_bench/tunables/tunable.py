#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tunable parameter definition.
"""
import copy
import collections
import logging

from typing import List, Optional, Tuple, TypedDict, Union

_LOG = logging.getLogger(__name__)


"""A tunable parameter value type alias."""
TunableValue = Union[int, float, str]


class TunableDict(TypedDict, total=False):
    """
    A typed dict for tunable parameters.

    Mostly used for mypy type checking.

    These are the types expected to be received from the json config.
    """

    type: str
    description: Optional[str]
    default: TunableValue
    values: Optional[List[str]]
    # For convenience, we allow the range to be specified as a list in the json, but recast it to a tuple internally.
    range: Optional[Union[Tuple[int, int], List[int], Tuple[float, float], List[float]]]
    special: Optional[Union[List[int], List[str]]]


class Tunable:  # pylint: disable=too-many-instance-attributes
    """
    A tunable parameter definition and its current value.
    """

    _TYPE = {
        "int": int,
        "float": float,
        "categorical": str,
    }

    def __init__(self, name: str, config: TunableDict):
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
        self._default = config["default"]
        self._values = config.get("values")
        self._range: Optional[Union[Tuple[int, int], Tuple[float, float]]] = None
        config_range = config.get("range")
        if config_range is not None:
            assert len(config_range) == 2, f"Invalid range: {config_range}"
            config_range = (config_range[0], config_range[1])
            self._range = config_range
        self._special = config.get("special")
        self._current_value = self._default
        if self.is_categorical:
            if not (self._values and isinstance(self._values, collections.abc.Iterable)):
                raise ValueError("Must specify values for the categorical type")
            if self._range is not None:
                raise ValueError("Range must be None for the categorical type")
            if self._special is not None:
                raise ValueError("Special values must be None for the categorical type")
        elif self.is_numerical:
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
        return bool(
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
    def value(self) -> TunableValue:
        """
        Get the current value of the tunable.
        """
        return self._current_value

    @value.setter
    def value(self, value: TunableValue) -> TunableValue:
        """
        Set the current value of the tunable.
        """
        # We need this coercion for the values produced by some optimizers
        # (e.g., scikit-optimize) and for data restored from certain storage
        # systems (where values can be strings).
        try:
            coerced_value = self._TYPE[self._type](value)
        except Exception:
            _LOG.error("Impossible conversion: %s %s <- %s %s",
                       self._type, self._name, type(value), value)
            raise

        if self._type == "int" and isinstance(value, float) and value != coerced_value:
            _LOG.error("Loss of precision: %s %s <- %s %s",
                       self._type, self._name, type(value), value)
            raise ValueError(f"Loss of precision: {self._name}={value}")

        if not self.is_valid(coerced_value):
            _LOG.error("Invalid assignment: %s %s <- %s %s",
                       self._type, self._name, type(value), value)
            raise ValueError(f"Invalid value for the tunable: {self._name}={value}")

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
        if self.is_categorical and self._values:
            return value in self._values
        elif self.is_numerical and self._range:
            return bool(self._range[0] <= value <= self._range[1]) or value == self._default
        else:
            raise ValueError(f"Invalid parameter type: {self._type}")

    @property
    def categorical_value(self) -> str:
        """
        Get the current value of the tunable as a number.
        """
        if self.is_categorical:
            return str(self._current_value)
        else:
            raise ValueError("Cannot get categorical values for a numerical tunable.")

    @property
    def numerical_value(self) -> Union[int, float]:
        """
        Get the current value of the tunable as a number.
        """
        if self._type == "int":
            return int(self._current_value)
        elif self._type == "float":
            return float(self._current_value)
        else:
            raise ValueError("Cannot get numerical value for a categorical tunable.")

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
    def is_categorical(self) -> bool:
        """
        Check if the tunable is categorical.

        Returns
        -------
        is_categorical : bool
            True if the tunable is categorical, False otherwise.
        """
        return self._type == "categorical"

    @property
    def is_numerical(self) -> bool:
        """
        Check if the tunable is an integer or float.

        Returns
        -------
        is_int : bool
            True if the tunable is an integer or float, False otherwise.
        """
        return self._type in {"int", "float"}

    @property
    def range(self) -> Union[Tuple[int, int], Tuple[float, float]]:
        """
        Get the range of the tunable if it is numerical, None otherwise.

        Returns
        -------
        range : (number, number)
            A 2-tuple of numbers that represents the range of the tunable.
            Numbers can be int or float, depending on the type of the tunable.
        """
        assert self.is_numerical
        assert self._range is not None
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
        assert self.is_categorical
        assert self._values is not None
        return self._values

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

from typing import Dict, List, Optional, Sequence, Tuple, Type, TypedDict, Union

_LOG = logging.getLogger(__name__)


"""A tunable parameter value type alias."""
TunableValue = Union[int, float, Optional[str]]


class TunableDict(TypedDict, total=False):
    """
    A typed dict for tunable parameters.

    Mostly used for mypy type checking.

    These are the types expected to be received from the json config.
    """

    type: str
    description: Optional[str]
    default: TunableValue
    values: Optional[List[Optional[str]]]
    range: Optional[Union[Sequence[int], Sequence[float]]]
    special: Optional[Union[List[int], List[str]]]


class Tunable:  # pylint: disable=too-many-instance-attributes
    """
    A tunable parameter definition and its current value.
    """

    # Maps tunable types to their corresponding Python types by name.
    _DTYPE: Dict[str, Type] = {
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
        self._sanity_check()

    def _sanity_check(self) -> None:
        """
        Check if the status of the Tunable is valid, and throw ValueError if it is not.
        """
        if self.is_categorical:
            if not (self._values and isinstance(self._values, collections.abc.Iterable)):
                raise ValueError("Must specify values for the categorical type")
            if self._range is not None:
                raise ValueError("Range must be None for the categorical type")
            if len(set(self._values)) != len(self._values):
                raise ValueError("Values must be unique for the categorical type")
            if self._special is not None:
                raise ValueError("Special values must be None for the categorical type")
        elif self.is_numerical:
            if self._values is not None:
                raise ValueError("Values must be None for the numerical type")
            if not self._range or len(self._range) != 2 or self._range[0] >= self._range[1]:
                raise ValueError(f"Invalid range: {self._range}")
        else:
            raise ValueError(f"Invalid parameter type: {self._type}")
        if not self.is_valid(self.default):
            raise ValueError(f"Invalid default value: {self.default}")

    def __repr__(self) -> str:
        """
        Produce a human-readable version of the Tunable (mostly for logging).

        Returns
        -------
        string : str
            A human-readable version of the Tunable.
        """
        return f"{self._name}={self._current_value}"

    def __eq__(self, other: object) -> bool:
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
        if not isinstance(other, Tunable):
            return False
        return bool(
            self._name == other._name and
            self._type == other._type and
            self._current_value == other._current_value
        )

    def __lt__(self, other: object) -> bool:    # pylint: disable=too-many-return-statements
        """
        Compare the two Tunable objects. We mostly need this to create a canonical list
        of tunable objects when hashing a TunableGroup.

        Parameters
        ----------
        other : Tunable
            A tunable object to compare to.

        Returns
        -------
        is_less : bool
            True if the current Tunable is less then the other one, False otherwise.
        """
        if not isinstance(other, Tunable):
            return False
        if self._name < other._name:
            return True
        if self._name == other._name and self._type < other._type:
            return True
        if self._name == other._name and self._type == other._type:
            if self.is_numerical:
                assert self._current_value is not None
                assert other._current_value is not None
                return bool(float(self._current_value) < float(other._current_value))
            # else: categorical
            if self._current_value is None:
                return True
            if other._current_value is None:
                return False
            return bool(str(self._current_value) < str(other._current_value))
        return False

    def copy(self) -> "Tunable":
        """
        Deep copy of the Tunable object.

        Returns
        -------
        tunable : Tunable
            A new Tunable object that is a deep copy of the original one.
        """
        return copy.deepcopy(self)

    @property
    def default(self) -> TunableValue:
        """
        Get the default value of the tunable.
        """
        return self._default

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
            if self.is_categorical and value is None:
                coerced_value = None
            else:
                coerced_value = self._DTYPE[self._type](value)
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

    def is_valid(self, value: TunableValue) -> bool:
        """
        Check if the value can be assigned to the tunable.

        Parameters
        ----------
        value : Union[int, float, str]
            Value to validate.

        Returns
        -------
        is_valid : bool
            True if the value is valid, False otherwise.
        """
        if self.is_categorical and self._values:
            return value in self._values
        elif self.is_numerical and self._range:
            if isinstance(value, (int, float)):
                # TODO: allow special values outside of range?
                return bool(self._range[0] <= value <= self._range[1])  # or value == self._default
            else:
                raise ValueError(f"Invalid value type for tunable {self}: {value}={type(value)}")
        else:
            raise ValueError(f"Invalid parameter type: {self._type}")

    @property
    def category(self) -> Optional[str]:
        """
        Get the current value of the tunable as a number.
        """
        if self.is_categorical:
            return None if self._current_value is None else str(self._current_value)
        else:
            raise ValueError("Cannot get categorical values for a numerical tunable.")

    @category.setter
    def category(self, new_value: Optional[str]) -> Optional[str]:
        """
        Set the current value of the tunable.
        """
        assert self.is_categorical
        assert isinstance(new_value, (str, type(None)))
        self.value = new_value
        return self.value

    @property
    def numerical_value(self) -> Union[int, float]:
        """
        Get the current value of the tunable as a number.
        """
        assert self._current_value is not None
        if self._type == "int":
            return int(self._current_value)
        elif self._type == "float":
            return float(self._current_value)
        else:
            raise ValueError("Cannot get numerical value for a categorical tunable.")

    @numerical_value.setter
    def numerical_value(self, new_value: Union[int, float]) -> Union[int, float]:
        """
        Set the current numerical value of the tunable.
        """
        # We need this coercion for the values produced by some optimizers
        # (e.g., scikit-optimize) and for data restored from certain storage
        # systems (where values can be strings).
        assert self.is_numerical
        self.value = new_value
        return self.value

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
    def dtype(self) -> Type:
        """
        Get the actual Python data type of the tunable.

        This is useful for bulk conversions of the input data.

        Returns
        -------
        dtype : type
            Data type of the tunable - one of {int, float, str}.
        """
        return self._DTYPE[self._type]

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
    def categories(self) -> List[Optional[str]]:
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

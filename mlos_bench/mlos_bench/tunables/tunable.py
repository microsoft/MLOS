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

from typing import Any, Dict, List, Optional, Sequence, Tuple, Type, TypedDict, Union

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
    special: Optional[Union[List[int], List[float]]]
    meta: Dict[str, Any]


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
        if '!' in name:  # TODO: Use a regex here and in JSON schema
            raise ValueError(f"Invalid name of the tunable: {name}")
        self._name = name
        self._type = config["type"]  # required
        if self._type not in self._DTYPE:
            raise ValueError(f"Invalid parameter type: {self._type}")
        self._description = config.get("description")
        self._default = config["default"]
        self._default = self.dtype(self._default) if self._default is not None else self._default
        self._values = config.get("values")
        if self._values:
            self._values = [str(v) if v is not None else v for v in self._values]
        self._meta: Dict[str, Any] = config.get("meta", {})
        self._range: Optional[Union[Tuple[int, int], Tuple[float, float]]] = None
        config_range = config.get("range")
        if config_range is not None:
            assert len(config_range) == 2, f"Invalid range: {config_range}"
            config_range = (config_range[0], config_range[1])
            self._range = config_range
        self._special: Union[List[int], List[float]] = config.get("special") or []
        self._current_value = None
        self._sanity_check()
        self.value = self._default

    def _sanity_check(self) -> None:
        """
        Check if the status of the Tunable is valid, and throw ValueError if it is not.
        """
        if self.is_categorical:
            if not (self._values and isinstance(self._values, collections.abc.Iterable)):
                raise ValueError(f"Must specify values for the categorical type tunable {self}")
            if self._range is not None:
                raise ValueError(f"Range must be None for the categorical type tunable {self}")
            if len(set(self._values)) != len(self._values):
                raise ValueError(f"Values must be unique for the categorical type tunable {self}")
            if self._special:
                raise ValueError(f"Categorical tunable cannot have special values: {self}")
        elif self.is_numerical:
            if self._values is not None:
                raise ValueError(f"Values must be None for the numerical type tunable {self}")
            if not self._range or len(self._range) != 2 or self._range[0] >= self._range[1]:
                raise ValueError(f"Invalid range for tunable {self}: {self._range}")
        else:
            raise ValueError(f"Invalid parameter type for tunable {self}: {self._type}")
        if not self.is_valid(self.default):
            raise ValueError(f"Invalid default value for tunable {self}: {self.default}")

    def __repr__(self) -> str:
        """
        Produce a human-readable version of the Tunable (mostly for logging).

        Returns
        -------
        string : str
            A human-readable version of the Tunable.
        """
        if self.is_categorical:
            return f"{self._name}[{self._type}]({self._values}:{self._default})={self._current_value}"
        return f"{self._name}[{self._type}]({self._range}:{self._default})={self._current_value}"

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

    def is_default(self) -> TunableValue:
        """
        Checks whether the currently assigned value of the tunable is at its default.
        """
        return self._default == self._current_value

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
                coerced_value = self.dtype(value)
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

    def update(self, value: TunableValue) -> bool:
        """
        Assign the value to the tunable. Return True if it is a new value, False otherwise.

        Parameters
        ----------
        value : Union[int, float, str]
            Value to assign.

        Returns
        -------
        is_updated : bool
            True if the new value is different from the previous one, False otherwise.
        """
        prev_value = self._current_value
        self.value = value
        return prev_value != self._current_value

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
                return self.in_range(value) or value in self._special
            else:
                raise ValueError(f"Invalid value type for tunable {self}: {value}={type(value)}")
        else:
            raise ValueError(f"Invalid parameter type: {self._type}")

    def in_range(self, value: Union[int, float, str, None]) -> bool:
        """
        Check if the value is within the range of the tunable.
        Do *NOT* check for special values.
        Return False if the tunable or value is categorical or None.
        """
        return (
            isinstance(value, (float, int)) and
            self.is_numerical and
            self._range is not None and
            bool(self._range[0] <= value <= self._range[1])
        )

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
    def special(self) -> Union[List[int], List[float]]:
        """
        Get the special values of the tunable. Return an empty list if there are none.

        Returns
        -------
        special : [int] | [float]
            A list of special values of the tunable. Can be empty.
        """
        return self._special

    @property
    def is_special(self) -> bool:
        """
        Check if the current value of the tunable is special.

        Returns
        -------
        is_special : bool
            True if the current value of the tunable is special, False otherwise.
        """
        return self.value in self._special

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

    @property
    def meta(self) -> Dict[str, Any]:
        """
        Get the tunable's metadata. This is a free-form dictionary that can be used to
        store any additional information about the tunable (e.g., the unit information).
        """
        return self._meta

#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Tunable parameter definition."""
import collections
import copy
import logging
from collections.abc import Iterable, Sequence
from typing import Any, Literal, TypedDict

import numpy as np

from mlos_bench.util import nullable

_LOG = logging.getLogger(__name__)

TunableValue = int | float | str | None
"""A tunable parameter value type alias."""

TunableValueType = type[int] | type[float] | type[str]
"""Tunable value type."""

TunableValueTypeTuple = (int, float, str, type(None))
"""
Tunable value type tuple.

For checking with isinstance()
"""

TunableValueTypeName = Literal["int", "float", "categorical"]
"""The string name of a tunable value type."""

TunableValuesDict = dict[str, TunableValue]
"""Tunable values dictionary type."""

DistributionName = Literal["uniform", "normal", "beta"]
"""Tunable value distribution type."""


class DistributionDict(TypedDict, total=False):
    """A typed dict for tunable parameters' distributions."""

    type: DistributionName
    params: dict[str, float] | None


class TunableDict(TypedDict, total=False):
    """
    A typed dict for tunable parameters.

    Mostly used for mypy type checking.

    These are the types expected to be received from the json config.
    """

    type: TunableValueTypeName
    description: str | None
    default: TunableValue
    values: list[str | None] | None
    range: Sequence[int] | Sequence[float] | None
    quantization_bins: int | None
    log: bool | None
    distribution: DistributionDict | None
    special: list[int] | list[float] | None
    values_weights: list[float] | None
    special_weights: list[float] | None
    range_weight: float | None
    meta: dict[str, Any]


class Tunable:  # pylint: disable=too-many-instance-attributes,too-many-public-methods
    """A tunable parameter definition and its current value."""

    # Maps tunable types to their corresponding Python types by name.
    _DTYPE: dict[TunableValueTypeName, TunableValueType] = {
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

        See Also
        --------
        :py:mod:`mlos_bench.tunables` : for more information on tunable parameters and
            their configuration.
        """
        if not isinstance(name, str) or "!" in name:  # TODO: Use a regex here and in JSON schema
            raise ValueError(f"Invalid name of the tunable: {name}")
        self._name = name
        self._type: TunableValueTypeName = config["type"]  # required
        if self._type not in self._DTYPE:
            raise ValueError(f"Invalid parameter type: {self._type}")
        self._description = config.get("description")
        self._default = config["default"]
        self._default = self.dtype(self._default) if self._default is not None else self._default
        self._values = config.get("values")
        if self._values:
            self._values = [str(v) if v is not None else v for v in self._values]
        self._meta: dict[str, Any] = config.get("meta", {})
        self._range: tuple[int, int] | tuple[float, float] | None = None
        self._quantization_bins: int | None = config.get("quantization_bins")
        self._log: bool | None = config.get("log")
        self._distribution: DistributionName | None = None
        self._distribution_params: dict[str, float] = {}
        distr = config.get("distribution")
        if distr:
            self._distribution = distr["type"]  # required
            self._distribution_params = distr.get("params") or {}
        config_range = config.get("range")
        if config_range is not None:
            assert len(config_range) == 2, f"Invalid range: {config_range}"
            config_range = (config_range[0], config_range[1])
            self._range = config_range
        self._special: list[int] | list[float] = config.get("special") or []
        self._weights: list[float] = (
            config.get("values_weights") or config.get("special_weights") or []
        )
        self._range_weight: float | None = config.get("range_weight")
        self._current_value = None
        self._sanity_check()
        self.value = self._default

    def _sanity_check(self) -> None:
        """Check if the status of the Tunable is valid, and throw ValueError if it is
        not.
        """
        if self.is_categorical:
            self._sanity_check_categorical()
        elif self.is_numerical:
            self._sanity_check_numerical()
        else:
            raise ValueError(f"Invalid parameter type for tunable {self}: {self._type}")
        if not self.is_valid(self.default):
            raise ValueError(f"Invalid default value for tunable {self}: {self.default}")

    def _sanity_check_categorical(self) -> None:
        """Check if the status of the categorical Tunable is valid, and throw ValueError
        if it is not.
        """
        # pylint: disable=too-complex
        assert self.is_categorical
        if not (self._values and isinstance(self._values, collections.abc.Iterable)):
            raise ValueError(f"Must specify values for the categorical type tunable {self}")
        if self._range is not None:
            raise ValueError(f"Range must be None for the categorical type tunable {self}")
        if len(set(self._values)) != len(self._values):
            raise ValueError(f"Values must be unique for the categorical type tunable {self}")
        if self._special:
            raise ValueError(f"Categorical tunable cannot have special values: {self}")
        if self._range_weight is not None:
            raise ValueError(f"Categorical tunable cannot have range_weight: {self}")
        if self._log is not None:
            raise ValueError(f"Categorical tunable cannot have log parameter: {self}")
        if self._quantization_bins is not None:
            raise ValueError(f"Categorical tunable cannot have quantization parameter: {self}")
        if self._distribution is not None:
            raise ValueError(f"Categorical parameters do not support `distribution`: {self}")
        if self._weights:
            if len(self._weights) != len(self._values):
                raise ValueError(f"Must specify weights for all values: {self}")
            if any(w < 0 for w in self._weights):
                raise ValueError(f"All weights must be non-negative: {self}")

    def _sanity_check_numerical(self) -> None:
        """Check if the status of the numerical Tunable is valid, and throw ValueError
        if it is not.
        """
        # pylint: disable=too-complex,too-many-branches
        assert self.is_numerical
        if self._values is not None:
            raise ValueError(f"Values must be None for the numerical type tunable {self}")
        if not self._range or len(self._range) != 2 or self._range[0] >= self._range[1]:
            raise ValueError(f"Invalid range for tunable {self}: {self._range}")
        if self._quantization_bins is not None and self._quantization_bins <= 1:
            raise ValueError(f"Number of quantization bins is <= 1: {self}")
        if self._distribution is not None and self._distribution not in {
            "uniform",
            "normal",
            "beta",
        }:
            raise ValueError(f"Invalid distribution: {self}")
        if self._distribution_params and self._distribution is None:
            raise ValueError(f"Must specify the distribution: {self}")
        if self._weights:
            if self._range_weight is None:
                raise ValueError(f"Must specify weight for the range: {self}")
            if len(self._weights) != len(self._special):
                raise ValueError("Must specify weights for all special values {self}")
            if any(w < 0 for w in self._weights + [self._range_weight]):
                raise ValueError(f"All weights must be non-negative: {self}")
        elif self._range_weight is not None:
            raise ValueError(f"Must specify both weights and range_weight or none: {self}")

    def __repr__(self) -> str:
        """
        Produce a human-readable version of the Tunable (mostly for logging).

        Returns
        -------
        string : str
            A human-readable version of the Tunable.
        """
        # TODO? Add weights, specials, quantization, distribution?
        if self.is_categorical:
            return (
                f"{self._name}[{self._type}]({self._values}:{self._default})={self._current_value}"
            )
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
            self._name == other._name
            and self._type == other._type
            and self._current_value == other._current_value
        )

    def __lt__(self, other: object) -> bool:  # pylint: disable=too-many-return-statements
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
        """Get the default value of the tunable."""
        return self._default

    def is_default(self) -> TunableValue:
        """Checks whether the currently assigned value of the tunable is at its
        default.
        """
        return self._default == self._current_value

    @property
    def value(self) -> TunableValue:
        """Get the current value of the tunable."""
        return self._current_value

    @value.setter
    def value(self, value: TunableValue) -> TunableValue:
        """Set the current value of the tunable."""
        # We need this coercion for the values produced by some optimizers
        # (e.g., scikit-optimize) and for data restored from certain storage
        # systems (where values can be strings).
        try:
            if self.is_categorical and value is None:
                coerced_value = None
            else:
                assert value is not None
                coerced_value = self.dtype(value)
        except Exception:
            _LOG.error(
                "Impossible conversion: %s %s <- %s %s",
                self._type,
                self._name,
                type(value),
                value,
            )
            raise

        if self._type == "int" and isinstance(value, float) and value != coerced_value:
            _LOG.error(
                "Loss of precision: %s %s <- %s %s",
                self._type,
                self._name,
                type(value),
                value,
            )
            raise ValueError(f"Loss of precision: {self._name}={value}")

        if not self.is_valid(coerced_value):
            _LOG.error(
                "Invalid assignment: %s %s <- %s %s",
                self._type,
                self._name,
                type(value),
                value,
            )
            raise ValueError(f"Invalid value for the tunable: {self._name}={value}")

        self._current_value = coerced_value
        return self._current_value

    def update(self, value: TunableValue) -> bool:
        """
        Assign the value to the tunable. Return True if it is a new value, False
        otherwise.

        Parameters
        ----------
        value : int | float | str
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
        value : int | float | str
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

    def in_range(self, value: int | float | str | None) -> bool:
        """
        Check if the value is within the range of the tunable.

        Do *NOT* check for special values. Return False if the tunable or value is
        categorical or None.
        """
        return (
            isinstance(value, (float, int))
            and self.is_numerical
            and self._range is not None
            and bool(self._range[0] <= value <= self._range[1])
        )

    @property
    def category(self) -> str | None:
        """Get the current value of the tunable as a string."""
        if self.is_categorical:
            return nullable(str, self._current_value)
        else:
            raise ValueError("Cannot get categorical values for a numerical tunable.")

    @category.setter
    def category(self, new_value: str | None) -> str | None:
        """Set the current value of the tunable."""
        assert self.is_categorical
        assert isinstance(new_value, (str, type(None)))
        self.value = new_value
        return self.value

    @property
    def numerical_value(self) -> int | float:
        """Get the current value of the tunable as a number."""
        assert self._current_value is not None
        if self._type == "int":
            return int(self._current_value)
        elif self._type == "float":
            return float(self._current_value)
        else:
            raise ValueError("Cannot get numerical value for a categorical tunable.")

    @numerical_value.setter
    def numerical_value(self, new_value: int | float) -> int | float:
        """Set the current numerical value of the tunable."""
        # We need this coercion for the values produced by some optimizers
        # (e.g., scikit-optimize) and for data restored from certain storage
        # systems (where values can be strings).
        assert self.is_numerical
        self.value = new_value
        return self.value

    @property
    def name(self) -> str:
        """Get the name / string ID of the tunable."""
        return self._name

    @property
    def special(self) -> list[int] | list[float]:
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
    def weights(self) -> list[float] | None:
        """
        Get the weights of the categories or special values of the tunable. Return None
        if there are none.

        Returns
        -------
        weights : [float]
            A list of weights or None.
        """
        return self._weights

    @property
    def range_weight(self) -> float | None:
        """
        Get weight of the range of the numeric tunable. Return None if there are no
        weights or a tunable is categorical.

        Returns
        -------
        weight : float
            Weight of the range or None.
        """
        assert self.is_numerical
        assert self._special
        assert self._weights
        return self._range_weight

    @property
    def type(self) -> TunableValueTypeName:
        """
        Get the data type of the tunable.

        Returns
        -------
        type : str
            Data type of the tunable - one of {'int', 'float', 'categorical'}.
        """
        return self._type

    @property
    def dtype(self) -> TunableValueType:
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
    def range(self) -> tuple[int, int] | tuple[float, float]:
        """
        Get the range of the tunable if it is numerical, None otherwise.

        Returns
        -------
        range : Union[tuple[int, int], tuple[float, float]]
            A 2-tuple of numbers that represents the range of the tunable.
            Numbers can be int or float, depending on the type of the tunable.
        """
        assert self.is_numerical
        assert self._range is not None
        return self._range

    @property
    def span(self) -> int | float:
        """
        Gets the span of the range.

        Note: this does not take quantization into account.

        Returns
        -------
        Union[int, float]
            (max - min) for numerical tunables.
        """
        num_range = self.range
        return num_range[1] - num_range[0]

    @property
    def quantization_bins(self) -> int | None:
        """
        Get the number of quantization bins, if specified.

        Returns
        -------
        quantization_bins : int | None
            Number of quantization bins, or None.
        """
        if self.is_categorical:
            return None
        return self._quantization_bins

    @property
    def quantized_values(self) -> Iterable[int] | Iterable[float] | None:
        """
        Get a sequence of quantized values for this tunable.

        Returns
        -------
        Optional[Union[Iterable[int], Iterable[float]]]
            If the Tunable is quantizable, returns a sequence of those elements,
            else None (e.g., for unquantized float type tunables).
        """
        num_range = self.range
        if self.type == "float":
            if not self.quantization_bins:
                return None
            # Be sure to return python types instead of numpy types.
            return (
                float(x)
                for x in np.linspace(
                    start=num_range[0],
                    stop=num_range[1],
                    num=self.quantization_bins,
                    endpoint=True,
                )
            )
        assert self.type == "int", f"Unhandled tunable type: {self}"
        return range(
            int(num_range[0]),
            int(num_range[1]) + 1,
            int(self.span / (self.quantization_bins - 1)) if self.quantization_bins else 1,
        )

    @property
    def cardinality(self) -> int | None:
        """
        Gets the cardinality of elements in this tunable, or else None. (i.e., when the
        tunable is continuous float and not quantized).

        If the tunable has quantization set, this

        Returns
        -------
        cardinality : int
            Either the number of points in the tunable or else None.
        """
        if self.is_categorical:
            return len(self.categories)
        if self.quantization_bins:
            return self.quantization_bins
        if self.type == "int":
            return int(self.span) + 1
        return None

    @property
    def is_log(self) -> bool | None:
        """
        Check if numeric tunable is log scale.

        Returns
        -------
        log : bool
            True if numeric tunable is log scale, False if linear.
        """
        assert self.is_numerical
        return self._log

    @property
    def distribution(self) -> DistributionName | None:
        """
        Get the name of the distribution (uniform, normal, or beta) if specified.

        Returns
        -------
        distribution : str
            Name of the distribution (uniform, normal, or beta) or None.
        """
        return self._distribution

    @property
    def distribution_params(self) -> dict[str, float]:
        """
        Get the parameters of the distribution, if specified.

        Returns
        -------
        distribution_params : dict[str, float]
            Parameters of the distribution or None.
        """
        assert self._distribution is not None
        return self._distribution_params

    @property
    def categories(self) -> list[str | None]:
        """
        Get the list of all possible values of a categorical tunable. Return None if the
        tunable is not categorical.

        Returns
        -------
        values : list[str]
            List of all possible values of a categorical tunable.
        """
        assert self.is_categorical
        assert self._values is not None
        return self._values

    @property
    def values(self) -> Iterable[str | None] | Iterable[int] | Iterable[float] | None:
        """
        Gets the categories or quantized values for this tunable.

        Returns
        -------
        Optional[Union[Iterable[Optional[str]], Iterable[int], Iterable[float]]]
            Categories or quantized values.
        """
        if self.is_categorical:
            return self.categories
        assert self.is_numerical
        return self.quantized_values

    @property
    def meta(self) -> dict[str, Any]:
        """
        Get the tunable's metadata.

        This is a free-form dictionary that can be used to store any additional
        information about the tunable (e.g., the unit information).
        """
        return self._meta

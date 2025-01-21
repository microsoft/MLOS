#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Definitions for :py:class:`~.Tunable` parameters.

Tunable parameters are one of the core building blocks of the :py:mod:`mlos_bench`
framework.
Together with :py:class:`~mlos_bench.tunables.tunable_groups.TunableGroups`, they
provide a description of a configuration parameter space for a benchmark or an
autotuning optimization task.

Some details about the configuration of an individual :py:class:`~.Tunable`
parameter are available in the Examples docstrings below.

However, Tunables are generally provided as a part of a
:py:class:`~mlos_bench.tunables.tunable_groups.TunableGroups` config specified in a
JSON config file.

See Also
--------
:py:mod:`mlos_bench.tunables` :
    For more information on Tunable parameters and their configuration.
"""
# pylint: disable=too-many-lines # lots of docstring examples

import copy
import logging
from collections.abc import Iterable
from typing import Any

import json5 as json
import numpy as np

from mlos_bench.config.schemas import ConfigSchema
from mlos_bench.tunables.tunable_types import (
    TUNABLE_DTYPE,
    DistributionName,
    TunableValue,
    TunableValueType,
    TunableValueTypeName,
    tunable_dict_from_dict,
)
from mlos_bench.util import nullable

_LOG = logging.getLogger(__name__)


class Tunable:  # pylint: disable=too-many-instance-attributes,too-many-public-methods
    """A Tunable parameter definition and its current value."""

    @staticmethod
    def from_json(name: str, json_str: str) -> "Tunable":
        """
        Create a Tunable object from a JSON string.

        Parameters
        ----------
        name : str
            Human-readable identifier of the Tunable parameter.
        json_str : str
            JSON string that represents a Tunable.

        Returns
        -------
        tunable : Tunable
            A new Tunable object created from the JSON string.

        Notes
        -----
        This is mostly for testing purposes.
        Generally Tunables will be created as a part of loading
        :py:class:`~mlos_bench.tunables.tunable_groups.TunableGroups`.

        See Also
        --------
        :py:meth:`ConfigPersistenceService.load_tunables <mlos_bench.services.config_persistence.ConfigPersistenceService.load_tunables>`
        """  # pylint: disable=line-too-long # noqa: E501
        config = json.loads(json_str)
        assert isinstance(config, dict)
        Tunable._validate_json_config(name, config)
        return Tunable(name, config)

    @staticmethod
    def _validate_json_config(name: str, config: dict) -> None:
        """
        Reconstructs a basic json config that this Tunable might have been constructed
        with via a TunableGroup for the purposes of schema validation so that we know
        our test cases are valid.

        Notes
        -----
        This is mostly for testing purposes, so we don't call it during normal
        Tunable instantiation since it's typically already been done by
        TunableGroups.
        """
        json_config = {
            "group": {
                "cost": 1,
                "params": {name: config},
            }
        }
        ConfigSchema.TUNABLE_PARAMS.validate(json_config)

    def __init__(self, name: str, config: dict):
        """
        Create an instance of a new Tunable parameter.

        Parameters
        ----------
        name : str
            Human-readable identifier of the Tunable parameter.
            NOTE: ``!`` characters are currently disallowed in Tunable names in order
            handle "special" values sampling logic.
            See: :py:mod:`mlos_bench.optimizers.convert_configspace` for details.
        config : dict
            Python dict that represents a Tunable (e.g., deserialized from JSON)
            NOTE: Must be convertible to a
            :py:class:`~mlos_bench.tunables.tunable_types.TunableDict`.

        See Also
        --------
        :py:mod:`mlos_bench.tunables` :
            For more information on Tunable parameters and their configuration.
        """
        t_config = tunable_dict_from_dict(config)
        if not isinstance(name, str) or "!" in name:  # TODO: Use a regex here and in JSON schema
            raise ValueError(f"Invalid name of the tunable: {name}")
        self._name = name
        self._type: TunableValueTypeName = t_config["type"]  # required
        if self._type not in TUNABLE_DTYPE:
            raise ValueError(f"Invalid parameter type: {self._type}")
        self._description = t_config.get("description")
        self._default = t_config["default"]
        self._default = self.dtype(self._default) if self._default is not None else self._default
        self._values = t_config.get("values")
        if self._values:
            self._values = [str(v) if v is not None else v for v in self._values]
        self._meta: dict[str, Any] = t_config.get("meta", {})
        self._range: tuple[int, int] | tuple[float, float] | None = None
        self._quantization_bins: int | None = t_config.get("quantization_bins")
        self._log: bool | None = t_config.get("log")
        self._distribution: DistributionName | None = None
        self._distribution_params: dict[str, float] = {}
        distr = t_config.get("distribution")
        if distr:
            self._distribution = distr["type"]  # required
            self._distribution_params = distr.get("params") or {}
        config_range = config.get("range")
        if config_range is not None:
            assert len(config_range) == 2, f"Invalid range: {config_range}"
            config_range = (config_range[0], config_range[1])
            self._range = config_range
        self._special: list[int] | list[float] = t_config.get("special") or []
        self._weights: list[float] = (
            t_config.get("values_weights") or t_config.get("special_weights") or []
        )
        self._range_weight: float | None = t_config.get("range_weight")
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
        if not (self._values and isinstance(self._values, Iterable)):
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
        Compare the two Tunable objects.

        We mostly need this to create a canonical list of Tunable objects when
        hashing a :py:class:`~mlos_bench.tunables.tunable_groups.TunableGroups`.

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
    def description(self) -> str | None:
        """Get the description of the Tunable."""
        return self._description

    @property
    def default(self) -> TunableValue:
        """Get the default value of the Tunable."""
        return self._default

    def is_default(self) -> bool:
        """Checks whether the currently assigned value of the Tunable is at its
        default.
        """
        return self._default == self._current_value

    @property
    def value(self) -> TunableValue:
        """Get the current value of the Tunable."""
        return self._current_value

    @value.setter
    def value(self, value: TunableValue) -> TunableValue:
        """Set the current value of the Tunable."""
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
            raise ValueError(f"Invalid value for the Tunable: {self._name}={value}")

        self._current_value = coerced_value
        return self._current_value

    def update(self, value: TunableValue) -> bool:
        """
        Assign the value to the Tunable. Return True if it is a new value, False
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
        Check if the value can be assigned to the Tunable.

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
                raise ValueError(f"Invalid value type for Tunable {self}: {value}={type(value)}")
        else:
            raise ValueError(f"Invalid parameter type: {self._type}")

    def in_range(self, value: int | float | str | None) -> bool:
        """
        Check if the value is within the range of the Tunable.

        Do *NOT* check for special values. Return False if the Tunable or value is
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
        """Get the current value of the Tunable as a string."""
        if self.is_categorical:
            return nullable(str, self._current_value)
        else:
            raise ValueError("Cannot get categorical values for a numerical Tunable.")

    @category.setter
    def category(self, new_value: str | None) -> str | None:
        """Set the current value of the Tunable."""
        assert self.is_categorical
        assert isinstance(new_value, (str, type(None)))
        self.value = new_value
        return self.value

    @property
    def numerical_value(self) -> int | float:
        """Get the current value of the Tunable as a number."""
        assert self._current_value is not None
        if self._type == "int":
            return int(self._current_value)
        elif self._type == "float":
            return float(self._current_value)
        else:
            raise ValueError("Cannot get numerical value for a categorical Tunable.")

    @numerical_value.setter
    def numerical_value(self, new_value: int | float) -> int | float:
        """Set the current numerical value of the Tunable."""
        # We need this coercion for the values produced by some optimizers
        # (e.g., scikit-optimize) and for data restored from certain storage
        # systems (where values can be strings).
        assert self.is_numerical
        self.value = new_value
        return self.value

    @property
    def name(self) -> str:
        """Get the name / string ID of the Tunable."""
        return self._name

    @property
    def special(self) -> list[int] | list[float]:
        """
        Get the special values of the Tunable. Return an empty list if there are none.

        Special values are used to mark some values as "special" that need more
        explicit testing. For example, these might indicate "automatic" or
        "disabled" behavior for the system being tested instead of an explicit size
        and hence need more explicit sampling.

        Notes
        -----
        Only numerical Tunable parameters can have special values.

        Returns
        -------
        special : [int] | [float]
            A list of special values of the Tunable. Can be empty.

        Examples
        --------
        >>> # Example values of the special values
        >>> json_config = '''
        ... {
        ...    "type": "int",
        ...    "default": 50,
        ...    "range": [1, 100],
        ...    // These are special and sampled
        ...    // Note that the types don't need to match or be in the range.
        ...    "special": [
        ...      -1,     // e.g., auto
        ...       0,     // e.g., disabled
        ...       true,  // e.g., enabled
        ...       null,  // e.g., unspecified
        ...    ],
        ... }
        ... '''
        >>> tunable = Tunable.from_json("tunable_with_special", json_config)
        >>> # JSON values are converted to Python types
        >>> tunable.special
        [-1, 0, True, None]
        """
        if not self.is_numerical:
            assert not self._special
            return []
        return self._special

    @property
    def is_special(self) -> bool:
        """
        Check if the current value of the Tunable is special.

        Returns
        -------
        is_special : bool
            True if the current value of the Tunable is special, False otherwise.
        """
        return self.value in self._special

    @property
    def weights(self) -> list[float] | None:
        """
        Get the weights of the categories or special values of the Tunable. Return None
        if there are none.

        Returns
        -------
        weights : [float]
            A list of weights or None.

        Examples
        --------
        >>> json_config = '''
        ... {
        ...    "type": "categorical",
        ...    "default": "red",
        ...    "values": ["red", "blue", "green"],
        ...    "values_weights": [0.1, 0.2, 0.7],
        ... }
        ... '''
        >>> categorical_tunable = Tunable.from_json("categorical_tunable", json_config)
        >>> categorical_tunable.weights
        [0.1, 0.2, 0.7]
        >>> dict(zip(categorical_tunable.values, categorical_tunable.weights))
        {'red': 0.1, 'blue': 0.2, 'green': 0.7}

        >>> json_config = '''
        ... {
        ...    "type": "float",
        ...    "default": 50.0,
        ...    "range": [1, 100],
        ...    "special": [-1, 0],
        ...    "special_weights": [0.1, 0.2],
        ...    "range_weight": 0.7,
        ... }
        ... '''
        >>> float_tunable = Tunable.from_json("float_tunable", json_config)
        >>> float_tunable.weights
        [0.1, 0.2]
        >>> dict(zip(float_tunable.special, float_tunable.weights))
        {-1: 0.1, 0: 0.2}
        """
        return self._weights

    @property
    def range_weight(self) -> float | None:
        """
        Get weight of the range of the numeric Tunable. Return None if there are no
        weights or a Tunable is categorical.

        Returns
        -------
        weight : float
            Weight of the range or None.

        See Also
        --------
        Tunable.weights : For example of range_weight configuration.
        """
        assert self.is_numerical
        assert self._special
        assert self._weights
        return self._range_weight

    @property
    def type(self) -> TunableValueTypeName:
        """
        Get the string name of the data type of the Tunable.

        Returns
        -------
        type : TunableValueTypeName
            String representation of the data type of the Tunable.

        Examples
        --------
        >>> # Example values of the TunableValueTypeName
        >>> from mlos_bench.tunables.tunable_types import TunableValueTypeName
        >>> TunableValueTypeName
        typing.Literal['int', 'float', 'categorical']

        Examples
        --------
        >>> json_config = '''
        ... {
        ...    "type": "categorical",
        ...    "default": "red",
        ...    "values": ["red", "blue", "green"],
        ... }
        ... '''
        >>> categorical_tunable = Tunable.from_json("categorical_tunable", json_config)
        >>> categorical_tunable.type
        'categorical'

        >>> json_config = '''
        ... {
        ...    "type": "int",
        ...    "default": 0,
        ...    "range": [0, 10000],
        ... }
        ... '''
        >>> int_tunable = Tunable.from_json("int_tunable", json_config)
        >>> int_tunable.type
        'int'

        >>> json_config = '''
        ... {
        ...    "type": "float",
        ...    "default": 0.0,
        ...    "range": [0.0, 10000.0],
        ... }
        ... '''
        >>> float_tunable = Tunable.from_json("float_tunable", json_config)
        >>> float_tunable.type
        'float'
        """
        return self._type

    @property
    def dtype(self) -> TunableValueType:
        """
        Get the actual Python data type of the Tunable.

        This is useful for bulk conversions of the input data.

        Returns
        -------
        dtype : type
            Data type of the Tunable - one of:
            ``{int, float, str}``

        Examples
        --------
        >>> # Example values of the TunableValueType
        >>> from mlos_bench.tunables.tunable_types import TunableValueType
        >>> TunableValueType
        type[int] | type[float] | type[str]

        >>> # Example values of the TUNABLE_DTYPE
        >>> from mlos_bench.tunables.tunable_types import TUNABLE_DTYPE
        >>> TUNABLE_DTYPE
        {'int': <class 'int'>, 'float': <class 'float'>, 'categorical': <class 'str'>}
        """
        return TUNABLE_DTYPE[self._type]

    @property
    def is_categorical(self) -> bool:
        """
        Check if the Tunable is categorical.

        Returns
        -------
        is_categorical : bool
            True if the Tunable is categorical, False otherwise.
        """
        return self._type == "categorical"

    @property
    def is_numerical(self) -> bool:
        """
        Check if the Tunable is an integer or float.

        Returns
        -------
        is_int : bool
            True if the Tunable is an integer or float, False otherwise.
        """
        return self._type in {"int", "float"}

    @property
    def range(self) -> tuple[int, int] | tuple[float, float]:
        """
        Get the range of the Tunable if it is numerical, None otherwise.

        Returns
        -------
        range : tuple[int, int] | tuple[float, float]
            A 2-tuple of numbers that represents the range of the Tunable.
            Numbers can be int or float, depending on the type of the Tunable.

        Examples
        --------
        >>> json_config = '''
        ... {
        ...    "type": "int",
        ...    "default": 0,
        ...    "range": [0, 10000],
        ... }
        ... '''
        >>> int_tunable = Tunable.from_json("int_tunable", json_config)
        >>> int_tunable.range
        (0, 10000)

        >>> json_config = '''
        ... {
        ...    "type": "float",
        ...    "default": 0.0,
        ...    "range": [0.0, 100.0],
        ... }
        ... '''
        >>> float_tunable = Tunable.from_json("float_tunable", json_config)
        >>> float_tunable.range
        (0.0, 100.0)
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
        int | float
            (max - min) for numerical Tunables.
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

        Examples
        --------
        >>> json_config = '''
        ... {
        ...    "type": "int",
        ...    "default": 0,
        ...    "range": [0, 10000],
        ...    // Enable quantization.
        ...    "quantization_bins": 11,
        ... }
        ... '''
        >>> quantized_tunable = Tunable.from_json("quantized_tunable", json_config)
        >>> quantized_tunable.quantization_bins
        11
        >>> list(quantized_tunable.quantized_values)
        [0, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000]

        >>> json_config = '''
        ... {
        ...    "type": "float",
        ...    "default": 0,
        ...    "range": [0, 1],
        ...    // Enable quantization.
        ...    "quantization_bins": 5,
        ... }
        ... '''
        >>> quantized_tunable = Tunable.from_json("quantized_tunable", json_config)
        >>> quantized_tunable.quantization_bins
        5
        >>> list(quantized_tunable.quantized_values)
        [0.0, 0.25, 0.5, 0.75, 1.0]
        """
        if self.is_categorical:
            return None
        return self._quantization_bins

    @property
    def quantized_values(self) -> Iterable[int] | Iterable[float] | None:
        """
        Get a sequence of quantized values for this Tunable.

        Returns
        -------
        Iterable[int] | Iterable[float] | None
            If the Tunable is quantizable, returns a sequence of those elements,
            else None (e.g., for unquantized float type Tunables).

        See Also
        --------
        :py:attr:`~.Tunable.quantization_bins` :
            For more examples on configuring a Tunable with quantization.
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
        assert self.type == "int", f"Unhandled Tunable type: {self}"
        return range(
            int(num_range[0]),
            int(num_range[1]) + 1,
            int(self.span / (self.quantization_bins - 1)) if self.quantization_bins else 1,
        )

    @property
    def cardinality(self) -> int | None:
        """
        Gets the cardinality of elements in this Tunable, or else None (e.g., when the
        Tunable is continuous float and not quantized).

        If the Tunable has quantization set, this returns the number of quantization bins.

        Returns
        -------
        cardinality : int
            Either the number of points in the Tunable or else None.

        Examples
        --------
        >>> json_config = '''
        ... {
        ...    "type": "categorical",
        ...    "default": "red",
        ...    "values": ["red", "blue", "green"],
        ... }
        ... '''
        >>> categorical_tunable = Tunable.from_json("categorical_tunable", json_config)
        >>> categorical_tunable.cardinality
        3

        >>> json_config = '''
        ... {
        ...    "type": "int",
        ...    "default": 0,
        ...    "range": [0, 10000],
        ... }
        ... '''
        >>> basic_tunable = Tunable.from_json("basic_tunable", json_config)
        >>> basic_tunable.cardinality
        10001

        >>> json_config = '''
        ... {
        ...    "type": "int",
        ...    "default": 0,
        ...    "range": [0, 10000],
        ...    // Enable quantization.
        ...    "quantization_bins": 10,
        ... }
        ... '''
        >>> quantized_tunable = Tunable.from_json("quantized_tunable", json_config)
        >>> quantized_tunable.cardinality
        10

        >>> json_config = '''
        ... {
        ...    "type": "float",
        ...    "default": 50.0,
        ...    "range": [0, 100],
        ... }
        ... '''
        >>> float_tunable = Tunable.from_json("float_tunable", json_config)
        >>> assert float_tunable.cardinality is None
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
        Check if numeric Tunable is log scale.

        Returns
        -------
        log : bool
            True if numeric Tunable is log scale, False if linear.

        Examples
        --------
        >>> # Example values of the log scale
        >>> json_config = '''
        ... {
        ...    "type": "int",
        ...    "default": 0,
        ...    "range": [0, 10000],
        ...    // Enable log sampling.
        ...    "log": true,
        ... }
        ... '''
        >>> tunable = Tunable.from_json("log_tunable", json_config)
        >>> tunable.is_log
        True
        """
        assert self.is_numerical
        return self._log

    @property
    def distribution(self) -> DistributionName | None:
        """
        Get the name of the distribution if specified.

        Returns
        -------
        distribution : str | None
            Name of the distribution or None.

        See Also
        --------
        :py:attr:`~.Tunable.distribution_params` :
            For more examples on configuring a Tunable with a distribution.

        Examples
        --------
        >>> # Example values of the DistributionName
        >>> from mlos_bench.tunables.tunable_types import DistributionName
        >>> DistributionName
        typing.Literal['uniform', 'normal', 'beta']
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

        Examples
        --------
        >>> json_config = '''
        ... {
        ...    "type": "int",
        ...    "default": 0,
        ...    "range": [0, 10],
        ...    // No distribution specified.
        ... }
        ... '''
        >>> base_config = json.loads(json_config)
        >>> basic_tunable = Tunable("basic_tunable", base_config)
        >>> assert basic_tunable.distribution is None
        >>> basic_tunable.distribution_params
        {}

        >>> # Example of a uniform distribution (the default if not specified)
        >>> config_with_dist = base_config | {
        ...    "distribution": {
        ...        "type": "uniform"
        ...    }
        ... }
        >>> uniform_tunable = Tunable("uniform_tunable", config_with_dist)
        >>> uniform_tunable.distribution
        'uniform'
        >>> uniform_tunable.distribution_params
        {}

        >>> # Example of a normal distribution params
        >>> config_with_dist = base_config | {
        ...    "distribution": {
        ...        "type": "normal",
        ...        "params": {
        ...            "mu": 0.0,
        ...            "sigma": 1.0,
        ...        }
        ...    }
        ... }
        >>> normal_tunable = Tunable("normal_tunable", config_with_dist)
        >>> normal_tunable.distribution
        'normal'
        >>> normal_tunable.distribution_params
        {'mu': 0.0, 'sigma': 1.0}

        >>> # Example of a beta distribution params
        >>> config_with_dist = base_config | {
        ...    "distribution": {
        ...        "type": "beta",
        ...        "params": {
        ...            "alpha": 1.0,
        ...            "beta": 1.0,
        ...        }
        ...    }
        ... }
        >>> beta_tunable = Tunable("beta_tunable", config_with_dist)
        >>> beta_tunable.distribution
        'beta'
        >>> beta_tunable.distribution_params
        {'alpha': 1.0, 'beta': 1.0}
        """
        return self._distribution_params

    @property
    def categories(self) -> list[str | None]:
        """
        Get the list of all possible values of a categorical Tunable. Return None if the
        Tunable is not categorical.

        Returns
        -------
        values : list[str]
            List of all possible values of a categorical Tunable.

        See Also
        --------
        Tunable.values : For more examples on getting the categorical values of a Tunable.
        """
        assert self.is_categorical
        assert self._values is not None
        return self._values

    @property
    def values(self) -> Iterable[str | None] | Iterable[int] | Iterable[float] | None:
        """
        Gets the :py:attr:`~.Tunable.categories` or
        :py:attr:`~.Tunable.quantized_values` for this Tunable.

        Returns
        -------
        Iterable[str | None] | Iterable[int] | Iterable[float] | None
            Categories or quantized values.

        Examples
        --------
        >>> # Example values of the Tunable categories
        >>> json_config = '''
        ... {
        ...    "type": "categorical",
        ...    "values": ["red", "blue", "green"],
        ...    "default": "red",
        ... }
        ... '''
        >>> categorical_tunable = Tunable.from_json("categorical_tunable", json_config)
        >>> list(categorical_tunable.values)
        ['red', 'blue', 'green']
        >>> assert categorical_tunable.values == categorical_tunable.categories

        >>> # Example values of the Tunable int
        >>> json_config = '''
        ... {
        ...    "type": "int",
        ...    "range": [0, 5],
        ...    "default": 1,
        ... }
        ... '''
        >>> int_tunable = Tunable.from_json("int_tunable", json_config)
        >>> list(int_tunable.values)
        [0, 1, 2, 3, 4, 5]

        >>> # Example values of the quantized Tunable float
        >>> json_config = '''
        ... {
        ...    "type": "float",
        ...    "range": [0, 1],
        ...    "default": 0.5,
        ...    "quantization_bins": 3,
        ... }
        ... '''
        >>> float_tunable = Tunable.from_json("float_tunable", json_config)
        >>> list(float_tunable.values)
        [0.0, 0.5, 1.0]
        """
        if self.is_categorical:
            return self.categories
        assert self.is_numerical
        return self.quantized_values

    @property
    def meta(self) -> dict[str, Any]:
        """
        Get the Tunable's metadata.

        This is a free-form dictionary that can be used to store any additional
        information about the Tunable (e.g., the unit information) which can be
        useful when using the ``dump_params_file`` and ``dump_meta_file``
        properties of the :py:class:`~mlos_bench.environments` config to
        generate a configuration file for the target system.

        Examples
        --------
        >>> json_config = '''
        ... {
        ...    "type": "int",
        ...    "range": [0, 10],
        ...    "default": 1,
        ...    "meta": {
        ...        "unit": "seconds",
        ...    },
        ...    "description": "Time to wait before timing out a request.",
        ... }
        ... '''
        >>> tunable = Tunable.from_json("timer_tunable", json_config)
        >>> tunable.meta
        {'unit': 'seconds'}
        """
        return self._meta

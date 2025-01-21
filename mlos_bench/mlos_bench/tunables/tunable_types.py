#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Helper types for :py:class:`~mlos_bench.tunables.tunable.Tunable`.

The main class of interest to most users in this module is :py:class:`.TunableDict`,
which provides the typed conversions from a JSON config to a config used for
creating a :py:class:`~mlos_bench.tunables.tunable.Tunable`.

The other types are mostly used for type checking and documentation purposes.
"""

# NOTE: pydoctest doesn't scan variable docstrings so we put the examples in the
# Tunable class docstrings.
# These type aliases are moved here mostly to allow easier documentation reading of
# the Tunable class itself.

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Literal, TypeAlias, TypedDict

if TYPE_CHECKING:
    # Used to allow for shorter docstring references.
    from mlos_bench.tunables.tunable import Tunable

TunableValue: TypeAlias = int | float | str | None
"""A :py:class:`TypeAlias` for a :py:class:`~.Tunable` parameter value."""

TunableValueType: TypeAlias = type[int] | type[float] | type[str]
"""A :py:class:`TypeAlias` for :py:class:`~.Tunable` value
:py:attr:`data type <.Tunable.dtype>`.

See Also
--------
:py:attr:`Tunable.dtype <.Tunable.dtype>` : Example of accepted types.
"""

TunableValueTypeTuple = (int, float, str, type(None))
"""
Tunable value ``type`` tuple.

Notes
-----
For checking whether a param is a :py:data:`.TunableValue` with
:py:func:`isinstance`.
"""

TunableValueTypeName = Literal["int", "float", "categorical"]
"""
The accepted string names of a :py:class:`~.Tunable` value :py:attr:`~.Tunable.type`.

See Also
--------
:py:attr:`Tunable.type <.Tunable.type>` : Example of accepted type names.
"""

TUNABLE_DTYPE: dict[TunableValueTypeName, TunableValueType] = {
    "int": int,
    "float": float,
    "categorical": str,
}
"""
Maps :py:class:`~.Tunable` types to their corresponding Python data types by name.

See Also
--------
:py:attr:`Tunable.dtype <.Tunable.dtype>` : Example of type mappings.
"""

TunableValuesDict = dict[str, TunableValue]
"""Tunable values dictionary type."""

DistributionName = Literal["uniform", "normal", "beta"]
"""
The :py:attr:`~.Tunable.distribution` type names for a :py:class:`~.Tunable` value.

See Also
--------
:py:attr:`Tunable.distribution <.Tunable.distribution>` :
    Example of accepted distribution names.
"""


class DistributionDictOpt(TypedDict, total=False):  # total=False allows for optional fields
    """
    A :py:class:`TypedDict` for a :py:class:`~.Tunable` parameter's optional
    :py:attr:`~.Tunable.distribution_params` config.

    Mostly used for type checking. These are the types expected to be received from
    the json config.

    Notes
    -----
    :py:class:`.DistributionDict` contains the required fields for the
    :py:attr:`Tunable.distribution <.Tunable.distribution>` parameter.

    See Also
    --------
    :py:attr:`Tunable.distribution_params <.Tunable.distribution_params>` :
        Examples of distribution parameters.
    """

    def __init__(self, *args, **kwargs):  # type: ignore # pylint: disable=useless-super-delegation
        """.. comment: don't inherit the docstring"""
        super().__init__(*args, **kwargs)

    params: dict[str, float] | None
    """
    The parameters for the distribution.

    See Also
    --------
    :py:attr:`Tunable.distribution_params <.Tunable.distribution_params>` :
        Examples of distribution parameters.
    """


class DistributionDict(DistributionDictOpt):
    """
    A :py:class:`TypedDict` for a :py:class:`~.Tunable` parameter's required
    :py:attr:`~.Tunable.distribution` config parameters.

    Mostly used for type checking. These are the types expected to be received from the
    json config.

    See Also
    --------
    :py:attr:`Tunable.distribution <.Tunable.distribution>` :
        Examples of Tunables with distributions.
    :py:attr:`Tunable.distribution_params <.Tunable.distribution_params>` :
        Examples of distribution parameters.
    """

    def __init__(self, *args, **kwargs):  # type: ignore # pylint: disable=useless-super-delegation
        """.. comment: don't inherit the docstring"""
        super().__init__(*args, **kwargs)

    type: DistributionName
    """
    The name of the distribution.

    See Also
    --------
    :py:attr:`Tunable.distribution <.Tunable.distribution>` :
        Examples of distribution names.
    """


class TunableDictOpt(TypedDict, total=False):  # total=False allows for optional fields
    """
    A :py:class:`TypedDict` for a :py:class:`~.Tunable` parameter's optional config
    parameters.

    Mostly used for type checking. These are the types expected to be received from
    the json config.

    Notes
    -----
    :py:class:`TunableDict` contains the required fields for the
    :py:class:`~.Tunable` parameter.
    """

    def __init__(self, *args, **kwargs):  # type: ignore # pylint: disable=useless-super-delegation
        """.. comment: don't inherit the docstring"""
        super().__init__(*args, **kwargs)

    # Optional fields:

    description: str | None
    """
    Description of the :py:class:`~.Tunable` parameter.

    See Also
    --------
    :py:attr:`Tunable.description <.Tunable.description>`
    """

    values: list[str | None] | None
    """
    List of values (or categories) for a "categorical" type :py:class:`~.Tunable`
    parameter.

    A list of values is required for "categorical" type Tunables.

    See Also
    --------
    :py:attr:`Tunable.categories <.Tunable.categories>`
    :py:attr:`Tunable.values <.Tunable.values>`
    """

    range: Sequence[int] | Sequence[float] | None
    """
    The range of values for an "int" or "float" type :py:class:`~.Tunable` parameter.

    Must be a sequence of two values: ``[min, max]``.

    A range is required for "int" and "float" type Tunables.

    See Also
    --------
    :py:attr:`Tunable.range <.Tunable.range>` : Examples of ranges.
    :py:attr:`Tunable.values <.Tunable.values>`
    """

    special: list[int] | list[float] | None
    """
    List of special values for an "int" or "float" type :py:class:`~.Tunable` parameter.

    These are values that are considered special by the target system (e.g.,
    ``null``, ``0``, ``-1``, ``auto``, etc.) and should be sampled with higher
    weights.

    See Also
    --------
    :py:attr:`Tunable.special <.Tunable.special>` : Examples of special values.
    """

    quantization_bins: int | None
    """
    The number of quantization bins for an "int" or "float" type :py:class:`~.Tunable`
    parameter.

    See Also
    --------
    :py:attr:`Tunable.quantization_bins <.Tunable.quantization_bins>` :
        Examples of quantized Tunables.
    """

    log: bool | None
    """
    Whether to use log sampling for an "int" or "float" type :py:class:`~.Tunable`
    parameter.

    See Also
    --------
    :py:attr:`Tunable.is_log <.Tunable.is_log>`
    """

    distribution: DistributionDict | None
    """
    Optional sampling distribution configuration for an "int" or "float" type
    :py:class:`~.Tunable` parameter.

    See Also
    --------
    :py:attr:`Tunable.distribution <.Tunable.distribution>` :
        Examples of distributions.
    :py:attr:`Tunable.distribution_params <.Tunable.distribution_params>` :
        Examples of distribution parameters.
    """

    values_weights: list[float] | None
    """
    Optional sampling weights for the values of a "categorical" type
    :py:class:`~.Tunable` parameter.

    See Also
    --------
    :py:attr:`Tunable.weights <.Tunable.weights>` : Examples of weighted sampling Tunables.
    """

    special_weights: list[float] | None
    """
    Optional sampling weights for the special values of an "int" or "float" type
    :py:class:`~.Tunable` parameter.

    See Also
    --------
    :py:attr:`Tunable.weights <.Tunable.weights>` : Examples of weighted sampling Tunables.
    """

    range_weight: float | None
    """
    Optional sampling weight for the main ranges of an "int" or "float" type
    :py:class:`~.Tunable` parameter.

    See Also
    --------
    :py:attr:`Tunable.range_weight <.Tunable.range_weight>` :
        Examples of weighted sampling Tunables.
    """

    meta: dict[str, Any]
    """
    Free form dict to store additional metadata for the :py:class:`~.Tunable` parameter
    (e.g., unit suffix, etc.)

    See Also
    --------
    :py:attr:`Tunable.meta <.Tunable.meta>` : Examples of Tunables with metadata.
    """


class TunableDict(TunableDictOpt):
    """
    A :py:class:`TypedDict` for a :py:class:`~.Tunable` parameter's required config
    parameters.

    Mostly used for type checking. These are the types expected to be received from
    the json config.

    Examples
    --------
    >>> # Example values of the TunableDict
    >>> TunableDict({'type': 'int', 'default': 0, 'range': [0, 10]})
    {'type': 'int', 'default': 0, 'range': [0, 10]}

    >>> # Example values of the TunableDict with optional fields
    >>> TunableDict({'type': 'categorical', 'default': 'a', 'values': ['a', 'b']})
    {'type': 'categorical', 'default': 'a', 'values': ['a', 'b']}
    """

    def __init__(self, *args, **kwargs):  # type: ignore # pylint: disable=useless-super-delegation
        """.. comment: don't inherit the docstring"""
        super().__init__(*args, **kwargs)

    # Required fields

    type: TunableValueTypeName
    """
    The name of the type of the :py:class:`~.Tunable` parameter.

    See Also
    --------
    :py:attr:`Tunable.type <.Tunable.type>` : Examples of type names.
    """

    default: TunableValue
    """
    The default value of the :py:class:`~.Tunable` parameter.

    See Also
    --------
    :py:attr:`Tunable.default <.Tunable.default>`
    """


def tunable_dict_from_dict(config: dict[str, Any]) -> TunableDict:
    """
    Creates a TunableDict from a regular dict.

    Notes
    -----
    Mostly used for type checking while instantiating a
    :py:class:`~.Tunable` from a json config.

    Parameters
    ----------
    config : dict[str, Any]
        A regular dict that represents a :py:class:`.TunableDict`.

    Returns
    -------
    TunableDict

    Examples
    --------
    >>> # Example values of the TunableDict
    >>> import json5 as json
    >>> config = json.loads("{'type': 'int', 'default': 0, 'range': [0, 10]}")
    >>> config
    {'type': 'int', 'default': 0, 'range': [0, 10]}
    >>> typed_dict = tunable_dict_from_dict(config)
    >>> typed_dict
    {'type': 'int', 'description': None, 'default': 0, 'values': None, 'range': [0, 10], 'quantization_bins': None, 'log': None, 'distribution': None, 'special': None, 'values_weights': None, 'special_weights': None, 'range_weight': None, 'meta': {}}
    """  # pylint: disable=line-too-long # noqa: E501
    _type = config.get("type")
    if _type not in TUNABLE_DTYPE:
        raise ValueError(f"Invalid parameter type: {_type}")
    _meta = config.get("meta", {})
    return TunableDict(
        type=_type,
        description=config.get("description"),
        default=config.get("default"),
        values=config.get("values"),
        range=config.get("range"),
        quantization_bins=config.get("quantization_bins"),
        log=config.get("log"),
        distribution=config.get("distribution"),
        special=config.get("special"),
        values_weights=config.get("values_weights"),
        special_weights=config.get("special_weights"),
        range_weight=config.get("range_weight"),
        meta=_meta,
    )

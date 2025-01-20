#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Helper types for :py:class:`~mlos_bench.tunables.tunable.Tunable`."""

# NOTE: pydoctest doesn't scan variable docstrings so we put the examples in the
# Tunable class docstrings.
# These type aliases are moved here mostly to allow easier documentation reading of
# the Tunable class itself.

from collections.abc import Sequence
from typing import Any, Literal, TypedDict

import json5 as json

TunableValue = int | float | str | None
"""A :py:class:`TypeAlias` for a :py:class:`mlos_bench.tunables.tunable.Tunable`
parameter value."""

TunableValueType = type[int] | type[float] | type[str]
"""A :py:class:`TypeAlias` for :py:class:`mlos_bench.tunables.tunable.Tunable` value
:py:attr:`data type <mlos_bench.tunables.tunable.Tunable.dtype>`.

See Also
--------
:py:attr:`Tunable.dtype <mlos_bench.tunables.tunable.Tunable.dtype>` : Example of
    accepted types.
"""

TunableValueTypeTuple = (int, float, str, type(None))
"""
Tunable value type tuple.

Notes
-----
For checking with :py:func:`isinstance`.
"""

TunableValueTypeName = Literal["int", "float", "categorical"]
"""
The accepted string names of a :py:class:`mlos_bench.tunables.tunable.Tunable` value
:py:attr:`~mlos_bench.tunables.tunable.Tunable.type`.

See Also
--------
:py:attr:`Tunable.type <mlos_bench.tunables.tunable.Tunable>` : Example of accepted
    type names.
"""

TUNABLE_DTYPE: dict[TunableValueTypeName, TunableValueType] = {
    "int": int,
    "float": float,
    "categorical": str,
}
"""
Maps :py:class:`~mlos_bench.tunables.tunable.Tunable` types to their corresponding
Python data types by name.

See Also
--------
:py:attr:`Tunable.dtype <mlos_bench.tunables.tunable.Tunable.dtype>` : Example of
    type mappings.
"""

TunableValuesDict = dict[str, TunableValue]
"""Tunable values dictionary type."""

DistributionName = Literal["uniform", "normal", "beta"]
"""
The :py:class:`~mlos_bench.tunables.tunable.Tunable` value
:py:attr:`~mlos_bench.tunables.tunable.Tunable.distribution` type names.

See Also
--------
:py:attr:`mlos_bench.tunables.tunable.Tunable.distribution` : Example of accepted
    distribution names.
"""


class DistributionDictOpt(TypedDict, total=False):  # total=False allows for optional fields
    """
    A TypedDict for a :py:class:`mlos_bench.tunables.tunable.Tunable` parameter's
    optional :py:attr:`~mlos_bench.tunables.tunable.Tunable.distribution_params` config.

    Mostly used for type checking. These are the types expected to be received from
    the json config.

    Notes
    -----
    :py:class:`.DistributionDict` contains the required fields for the
    :py:class:`mlos_bench.tunables.tunable.Tunable` 's
    :py:attr:`~mlos_bench.tunables.tunable.Tunable.distribution` parameter.

    See Also
    --------
    :py:attr:`mlos_bench.tunables.tunable.Tunable.distribution_params` : Example of
        distribution params.
    """

    params: dict[str, float] | None


class DistributionDict(DistributionDictOpt):
    """
    A TypedDict for a :py:class:`mlos_bench.tunables.tunable.Tunable` parameter's
    required ``distribution`` 's config parameters.

    Mostly used for type checking. These are the types expected to be received from the
    json config.

    See Also
    --------
    :py:attr:`mlos_bench.tunables.tunable.Tunable.distribution` : Example of
        distributions.
    :py:attr:`mlos_bench.tunables.tunable.Tunable.distribution_params` : Example of
        distribution params.
    """

    type: DistributionName


class TunableDictOpt(TypedDict, total=False):  # total=False allows for optional fields
    """
    A TypedDict for a :py:class:`mlos_bench.tunables.tunable.Tunable` parameter's
    optional config parameters.

    Mostly used for type checking. These are the types expected to be received from
    the json config.

    Notes
    -----
    :py:class:`TunableDict` contains the required fields for the
    :py:class:`mlos_bench.tunables.tunable.Tunable` parameter.
    """

    # Optional fields:

    description: str | None
    """
    Description of the :py:class:`mlos_bench.tunables.tunable.Tunable` parameter.

    See Also
    --------
    :py:attr:`Tunable.description <mlos_bench.tunables.tunable.Tunable.description>`
    """

    values: list[str | None] | None
    """
    List of values (or categories) for a "categorical" type
    :py:class:`mlos_bench.tunables.tunable.Tunable` parameter.

    A list of values is required for "categorical" type Tunables.

    See Also
    --------
    :py:attr:`Tunable.categories <mlos_bench.tunables.tunable.Tunable.categories>`
    :py:attr:`Tunable.values <mlos_bench.tunables.tunable.Tunable.values>`
    """

    range: Sequence[int] | Sequence[float] | None
    """
    The range of values for an "int" or "float" type
    :py:class:`mlos_bench.tunables.tunable.Tunable` parameter.

    Must be a sequence of two values: ``[min, max]``.

    A range is required for "int" and "float" type Tunables.

    See Also
    --------
    :py:attr:`Tunable.range <mlos_bench.tunables.tunable.Tunable.range>`
    :py:attr:`Tunable.values <mlos_bench.tunables.tunable.Tunable.values>`
    """

    special: list[int] | list[float] | None
    """
    List of special values for the :py:class:`mlos_bench.tunables.tunable.Tunable`
    parameter.

    These are values that are considered special by the target system (e.g.,
    ``null``, ``0``, ``-1``, ``auto``, etc.) and should be sampled with higher
    weights.

    See Also
    --------
    :py:attr:`Tunable.special <mlos_bench.tunables.tunable.Tunable.special>`
    """

    quantization_bins: int | None
    """
    The number of quantization bins for an "int" or "float" type
    :py:class:`mlos_bench.tunables.tunable.Tunable` parameter.

    See Also
    --------
    :py:attr:`Tunable.quantization_bins <mlos_bench.tunables.tunable.Tunable.quantization_bins>`
    """

    log: bool | None
    """
    Whether to use log sampling for an "int" or "float" type
    :py:class:`mlos_bench.tunables.tunable.Tunable` parameter.

    See Also
    --------
    :py:attr:`Tunable.is_log <mlos_bench.tunables.tunable.Tunable.is_log>`
    """

    distribution: DistributionDict | None
    """
    Optional sampling distribution configuration for an "int" or "float" type
    :py:class:`mlos_bench.tunables.tunable.Tunable` parameter.

    See Also
    --------
    :py:attr:`Tunable.distribution <mlos_bench.tunables.tunable.Tunable.distribution>` : Example
        of distributions.
    :py:attr:`Tunable.distribution_params <mlos_bench.tunables.tunable.Tunable.distribution_params>` : Example
        of distribution params.
    """  # pylint: disable=line-too-long # noqa: E501

    values_weights: list[float] | None
    """
    Optional sampling weights for the values of a "categorical" type
    :py:class:`mlos_bench.tunables.tunable.Tunable` parameter.

    See Also
    --------
    :py:attr:`Tunable.values_weights <mlos_bench.tunables.tunable.Tunable.values_weights>`
    """

    special_weights: list[float] | None
    """
    Optional sampling weights for the special values of a
    :py:class:`mlos_bench.tunables.tunable.Tunable` parameter.

    See Also
    --------
    :py:attr:`Tunable.special_weights <mlos_bench.tunables.tunable.Tunable.special_weights>`
    """

    range_weight: float | None
    """
    Optional sampling weight for the main ranges of an "int" or "float" type
    :py:class:`mlos_bench.tunables.tunable.Tunable` parameter.

    See Also
    --------
    :py:attr:`Tunable.range_weight <mlos_bench.tunables.tunable.Tunable.range_weight>`
    """

    meta: dict[str, Any]
    """
    Free form dict to store additional metadata for the
    :py:class:`mlos_bench.tunables.tunable.Tunable` parameter (e.g., unit suffix, etc.)

    See Also
    --------
    :py:attr:`Tunable.meta <mlos_bench.tunables.tunable.Tunable.meta>`
    """


class TunableDict(TunableDictOpt):
    """
    A TypedDict for a :py:class:`mlos_bench.tunables.tunable.Tunable` parameter's
    required config parameters.

    Mostly used for type checking. These are the types expected to be received from
    the json config.

    Examples
    --------
    >>> # Example values of the TunableDict
    >>> from mlos_bench.tunables.tunable import TunableDict
    >>> TunableDict({'type': 'int', 'default': 0, 'range': [0, 10]})
    {'type': 'int', 'default': 0, 'range': [0, 10]}

    >>> # Example values of the TunableDict with optional fields
    >>> TunableDict({'type': 'categorical', 'default': 'a', 'values': ['a', 'b']})
    {'type': 'categorical', 'default': 'a', 'values': ['a', 'b']}
    """

    # TODO: Add docstrings for this fields that refer to *working* examples in the Tunable class.

    # Required fields
    type: TunableValueTypeName
    """
    The name of the type of the :py:class:`mlos_bench.tunables.tunable.Tunable`
    parameter.

    See Also
    --------
    :py:attr:`Tunable.type <mlos_bench.tunables.tunable.Tunable.type>` : Examples of type names.
    """

    default: TunableValue
    """
    The default value of the :py:class:`mlos_bench.tunables.tunable.Tunable` parameter.

    See Also
    --------
    :py:attr:`Tunable.default <mlos_bench.tunables.tunable.Tunable.default>`
    """


def tunable_dict_from_dict(config: dict[str, Any]) -> TunableDict:
    """
    Creates a TunableDict from a regular dict.

    Notes
    -----
    Mostly used for type checking while instantiating a
    :py:class:`mlos_bench.tunables.tunable.Tunable` from a json config.

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
    >>> from mlos_bench.tunables.tunable_types import tunable_dict_from_dict
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


def tunable_dict_from_json(json_config: str) -> TunableDict:
    """
    Creates a TunableDict from a json string.

    Notes
    -----
    Just a convenient wrapper around :py:func:`json.loads` and
    :py:func:`.tunable_dict_from_dict`.

    Parameters
    ----------
    json_config : str
        A json string that represents a :py:class:`.TunableDict`.

    Returns
    -------
    TunableDict
    """
    config = json.loads(json_config)
    assert isinstance(config, dict)
    return tunable_dict_from_dict(config)

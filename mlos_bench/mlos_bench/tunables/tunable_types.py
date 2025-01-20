#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Helper types for :py:class:`~mlos_bench.tunables.tunable.Tunable`.
"""

# NOTE: pydoctest doesn't scan variable docstrings so we put the examples in the
# Tunable class docstrings.
# These type aliases are moved here mostly to allow easier documentation reading of
# the Tunable class itself.

from collections.abc import Sequence
from typing import Any, Literal, TypedDict

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
    optional :py:attr:`~mlos_bench.tunables.tunable.Tunable.distribution_params`
    config.

    Mostly used by type checking. These are the types expected to be received from
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

        Mostly used by type checking. These are the types expected to be received from the
        json config.

        Examples
        --------
        >>> # Example values of the DistributionName
        >>> from mlos_bench.tunables.tunable import DistributionName
        >>> DistributionName
        typing.Literal['uniform', 'normal', 'beta']

        >>> # Example values of the DistributionDict
        >>> from mlos_bench.tunables.tunable import DistributionDict
        >>> DistributionDict({'type': 'uniform'})
        {'type': 'uniform'}
        >>> DistributionDict({'type': 'normal', 'params': {'mu': 0.0, 'sigma': 1.0}})
        {'type': 'normal', 'params': {'mu': 0.0, 'sigma': 1.0}}
        >>> DistributionDict({'type': 'beta', 'params': {'alpha': 1.0, 'beta': 1.0}})
        {'type': 'beta', 'params': {'alpha': 1.0, 'beta': 1.0}}

    TODO: Remove those examples.

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

    # TODO: Add docstrings for this fields that refer to *working* examples in the Tunable class.

    # Optional fields
    description: str | None
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
    default: TunableValue


def tunable_dict_from_dict(config: dict[str, Any]) -> TunableDict:
    """
    Creates a TunableDict from a regular dict.

    Parameters
    ----------
    config : dict[str, Any]
        A regular dict that represents a TunableDict.

    Returns
    -------
    TunableDict

    Examples
    --------
    >>> # Example values of the TunableDict
    >>> import json5 as json
    >>> from mlos_bench.tunables.tunable import tunable_dict_from_dict
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

#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Basic initializer module for the mlos_core space adapters.
"""

from enum import Enum
from typing import Optional, TypeVar

import ConfigSpace

from mlos_core.spaces.adapters.llamatune import LlamaTuneAdapter

__all__ = [
    'LlamaTuneAdapter',
]


class SpaceAdapterType(Enum):
    """Enumerate supported MlosCore space adapters."""

    IDENTITY = None
    """A no-op adapter will be used"""

    LLAMATUNE = LlamaTuneAdapter
    """An instance of LlamaTuneAdapter class will be used"""


ConcreteSpaceAdapter = TypeVar('ConcreteSpaceAdapter', *[member.value for member in SpaceAdapterType])


class SpaceAdapterFactory:
    """Simple factory class for creating BaseSpaceAdapter-derived objects"""

    # pylint: disable=too-few-public-methods,consider-alternative-union-syntax

    @staticmethod
    def create(
        parameter_space: ConfigSpace.ConfigurationSpace,
        space_adapter_type: SpaceAdapterType = SpaceAdapterType.IDENTITY,
        space_adapter_kwargs: Optional[dict] = None,
    ) -> ConcreteSpaceAdapter:
        """Creates a new space adapter instance, given the parameter space and potential space adapter options.

        Parameters
        ----------
        parameter_space : ConfigSpace.ConfigurationSpace
            Input configuration space.

        space_adapter_type : Optional[SpaceAdapterType]
            Space adapter class to be used alongside the optimizer.

        space_adapter_kwargs : Optional[dict]
            Optional arguments passed in SpaceAdapter class constructor.

        Returns
        -------
        Instance of concrete optimizer (e.g., None, LlamaTuneAdapter, etc.)
        """
        if space_adapter_type is None or space_adapter_type is SpaceAdapterType.IDENTITY:
            return None
        if space_adapter_kwargs is None:
            space_adapter_kwargs = {}
        return space_adapter_type.value(parameter_space, **space_adapter_kwargs)

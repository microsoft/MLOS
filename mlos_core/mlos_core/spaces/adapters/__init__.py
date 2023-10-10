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

from mlos_core.spaces.adapters.identity_adapter import IdentityAdapter
from mlos_core.spaces.adapters.llamatune import LlamaTuneAdapter

__all__ = [
    'IdentityAdapter',
    'LlamaTuneAdapter',
]


class SpaceAdapterType(Enum):
    """Enumerate supported MlosCore space adapters."""

    IDENTITY = IdentityAdapter
    """A no-op adapter will be used"""

    LLAMATUNE = LlamaTuneAdapter
    """An instance of LlamaTuneAdapter class will be used"""


# To make mypy happy, we need to define a type variable for each optimizer type.
# https://github.com/python/mypy/issues/12952
# ConcreteSpaceAdapter = TypeVar('ConcreteSpaceAdapter', *[member.value for member in SpaceAdapterType])
# To address this, we add a test for complete coverage of the enum.
ConcreteSpaceAdapter = TypeVar(
    'ConcreteSpaceAdapter',
    IdentityAdapter,
    LlamaTuneAdapter,
)


class SpaceAdapterFactory:
    """Simple factory class for creating BaseSpaceAdapter-derived objects"""

    # pylint: disable=too-few-public-methods

    @staticmethod
    def create(*,
               parameter_space: ConfigSpace.ConfigurationSpace,
               space_adapter_type: SpaceAdapterType = SpaceAdapterType.IDENTITY,
               space_adapter_kwargs: Optional[dict] = None) -> ConcreteSpaceAdapter:    # type: ignore[type-var]
        """
        Create a new space adapter instance, given the parameter space and potential
        space adapter options.

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
        space_adapter : ConcreteSpaceAdapter
            Instance of concrete space adapter (e.g., None, LlamaTuneAdapter, etc.)
        """
        if space_adapter_type is None:
            space_adapter_type = SpaceAdapterType.IDENTITY
        if space_adapter_kwargs is None:
            space_adapter_kwargs = {}

        space_adapter: ConcreteSpaceAdapter = space_adapter_type.value(
            orig_parameter_space=parameter_space,
            **space_adapter_kwargs
        )

        return space_adapter

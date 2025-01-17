#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Basic initializer module for the mlos_core space adapters.

Space adapters provide a mechanism for automatic transformation of the original
:py:class:`ConfigSpace.ConfigurationSpace` provided to the optimizer into a new
space that is more suitable for the optimizer.

By default the :py:class:`.IdentityAdapter` is used, which does not perform any
transformation.
But, for instance, the :py:class:`.LlamaTuneAdapter` can be used to automatically
transform the space to a lower dimensional one.

See the :py:mod:`mlos_bench.optimizers.mlos_core_optimizer` module for more
information on how to do this with :py:mod:`mlos_bench`.

This module provides a simple :py:class:`.SpaceAdapterFactory` class to
:py:meth:`~.SpaceAdapterFactory.create` space adapters.

Examples
--------
TODO: Add example usage here.

Notes
-----
See `mlos_core/spaces/adapters/README.md
<https://github.com/microsoft/MLOS/tree/main/mlos_core/mlos_core/spaces/adapters>`_
for additional documentation and examples in the source tree.
"""

from enum import Enum

import ConfigSpace

from mlos_core.spaces.adapters.identity_adapter import IdentityAdapter
from mlos_core.spaces.adapters.llamatune import LlamaTuneAdapter

__all__ = [
    "ConcreteSpaceAdapter",
    "IdentityAdapter",
    "LlamaTuneAdapter",
    "SpaceAdapterFactory",
    "SpaceAdapterType",
]


class SpaceAdapterType(Enum):
    """Enumerate supported mlos_core space adapters."""

    IDENTITY = IdentityAdapter
    """A no-op adapter (:class:`.IdentityAdapter`) will be used."""

    LLAMATUNE = LlamaTuneAdapter
    """An instance of :class:`.LlamaTuneAdapter` class will be used."""


ConcreteSpaceAdapter = IdentityAdapter | LlamaTuneAdapter
"""Type alias for concrete SpaceAdapter classes (e.g.,
:class:`~mlos_core.spaces.adapters.identity_adapter.IdentityAdapter`, etc.)
"""


class SpaceAdapterFactory:
    """Simple factory class for creating
    :class:`~mlos_core.spaces.adapters.adapter.BaseSpaceAdapter`-derived objects.
    """

    # pylint: disable=too-few-public-methods

    @staticmethod
    def create(
        *,
        parameter_space: ConfigSpace.ConfigurationSpace,
        space_adapter_type: SpaceAdapterType | None = SpaceAdapterType.IDENTITY,
        space_adapter_kwargs: dict | None = None,
    ) -> ConcreteSpaceAdapter:
        """
        Create a new space adapter instance, given the parameter space and potential
        space adapter options.

        Parameters
        ----------
        parameter_space : ConfigSpace.ConfigurationSpace
            Input configuration space.
        space_adapter_type : SpaceAdapterType | None
            Space adapter class to be used alongside the optimizer.
        space_adapter_kwargs : dict | None
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
            **space_adapter_kwargs,
        )

        return space_adapter

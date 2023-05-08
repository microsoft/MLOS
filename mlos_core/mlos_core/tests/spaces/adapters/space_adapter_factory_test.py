#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tests for space adapter factory.
"""

# pylint: disable=missing-function-docstring

from typing import List, Optional, Type

import pytest

import ConfigSpace as CS

from mlos_core.spaces.adapters import SpaceAdapterFactory, SpaceAdapterType, ConcreteSpaceAdapter
from mlos_core.spaces.adapters.adapter import BaseSpaceAdapter
from mlos_core.spaces.adapters.identity_adapter import IdentityAdapter

from mlos_core.tests import get_all_subclasses


@pytest.mark.parametrize(('space_adapter_type'), [
    # Enumerate all supported SpaceAdapters
    # *[member for member in SpaceAdapterType],
    *list(SpaceAdapterType),
])
def test_concrete_optimizer_type(space_adapter_type: SpaceAdapterType) -> None:
    """
    Test that all optimizer types are listed in the ConcreteOptimizer constraints.
    """
    # pylint: disable=no-member
    assert space_adapter_type.value in ConcreteSpaceAdapter.__constraints__     # type: ignore[attr-defined]


@pytest.mark.parametrize(('space_adapter_type', 'kwargs'), [
    # Default space adapter
    (None, {}),
    # Enumerate all supported Optimizers
    *[(member, {}) for member in SpaceAdapterType],
])
def test_create_space_adapter_with_factory_method(space_adapter_type: Optional[SpaceAdapterType], kwargs: Optional[dict]) -> None:
    # Start defining a ConfigurationSpace for the Optimizer to search.
    input_space = CS.ConfigurationSpace(seed=1234)

    # Add a single continuous input dimension between 0 and 1.
    input_space.add_hyperparameter(CS.UniformFloatHyperparameter(name='x', lower=0, upper=1))
    # Add a single continuous input dimension between 0 and 1.
    input_space.add_hyperparameter(CS.UniformFloatHyperparameter(name='y', lower=0, upper=1))

    # Adjust some kwargs for specific space adapters
    if space_adapter_type is SpaceAdapterType.LLAMATUNE:
        if kwargs is None:
            kwargs = {}
        kwargs.setdefault('num_low_dims', 1)

    space_adapter: BaseSpaceAdapter
    if space_adapter_type is None:
        space_adapter = SpaceAdapterFactory.create(input_space)
    else:
        space_adapter = SpaceAdapterFactory.create(input_space, space_adapter_type, space_adapter_kwargs=kwargs)

    if space_adapter_type is None or space_adapter_type is SpaceAdapterType.IDENTITY:
        assert isinstance(space_adapter, IdentityAdapter)
    else:
        assert space_adapter is not None
        assert space_adapter.orig_parameter_space is not None
        myrepr = repr(space_adapter)
        assert myrepr.startswith(space_adapter_type.value.__name__), \
            f"Expected {space_adapter_type.value.__name__} but got {myrepr}"


# Dynamically determine all of the optimizers we have implemented.
space_adapter_subclasses: List[Type[BaseSpaceAdapter]] = [subclass for subclass in get_all_subclasses(BaseSpaceAdapter)
                                                   if issubclass(subclass, BaseSpaceAdapter) and not subclass.__abstractmethods__]


# Make sure they they're listed in the OptimizerType enum.
@pytest.mark.parametrize(('space_adapter_class'), space_adapter_subclasses)
def test_space_adapter_type_defs(space_adapter_class: type) -> None:
    """
    Test that all optimizer classes are listed in the OptimizerType enum.
    """
    for space_adapter_type in SpaceAdapterType:
        if space_adapter_type.value == space_adapter_class:
            return
    raise NotImplementedError("Missing SpaceAdapterType definition for space adapter class: " + space_adapter_class.__name__)

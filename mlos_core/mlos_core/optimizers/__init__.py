#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Basic initializer module for the mlos_core optimizers.
"""

from enum import Enum
from typing import Optional, TypeVar

import ConfigSpace

from mlos_core.optimizers.optimizer import BaseOptimizer
from mlos_core.optimizers.random_optimizer import RandomOptimizer
from mlos_core.optimizers.bayesian_optimizers.smac_optimizer import SmacOptimizer
from mlos_core.optimizers.flaml_optimizer import FlamlOptimizer
from mlos_core.spaces.adapters import SpaceAdapterType, SpaceAdapterFactory

__all__ = [
    'SpaceAdapterType',
    'OptimizerFactory',
    'BaseOptimizer',
    'RandomOptimizer',
    'FlamlOptimizer',
    'SmacOptimizer',
]


class OptimizerType(Enum):
    """Enumerate supported MlosCore optimizers."""

    RANDOM = RandomOptimizer
    """An instance of RandomOptimizer class will be used"""

    FLAML = FlamlOptimizer
    """An instance of FlamlOptimizer class will be used"""

    SMAC = SmacOptimizer
    """An instance of SmacOptimizer class will be used"""


# To make mypy happy, we need to define a type variable for each optimizer type.
# https://github.com/python/mypy/issues/12952
# ConcreteOptimizer = TypeVar('ConcreteOptimizer', *[member.value for member in OptimizerType])
# To address this, we add a test for complete coverage of the enum.
ConcreteOptimizer = TypeVar(
    'ConcreteOptimizer',
    RandomOptimizer,
    FlamlOptimizer,
    SmacOptimizer,
)

DEFAULT_OPTIMIZER_TYPE = OptimizerType.FLAML


class OptimizerFactory:
    """Simple factory class for creating BaseOptimizer-derived objects"""

    # pylint: disable=too-few-public-methods

    @staticmethod
    def create(*,
               parameter_space: ConfigSpace.ConfigurationSpace,
               optimizer_type: OptimizerType = DEFAULT_OPTIMIZER_TYPE,
               optimizer_kwargs: Optional[dict] = None,
               space_adapter_type: SpaceAdapterType = SpaceAdapterType.IDENTITY,
               space_adapter_kwargs: Optional[dict] = None) -> ConcreteOptimizer:   # type: ignore[type-var]
        """
        Create a new optimizer instance, given the parameter space, optimizer type,
        and potential optimizer options.

        Parameters
        ----------
        parameter_space : ConfigSpace.ConfigurationSpace
            Input configuration space.
        optimizer_type : OptimizerType
            Optimizer class as defined by Enum.
        optimizer_kwargs : Optional[dict]
            Optional arguments passed in Optimizer class constructor.
        space_adapter_type : Optional[SpaceAdapterType]
            Space adapter class to be used alongside the optimizer.
        space_adapter_kwargs : Optional[dict]
            Optional arguments passed in SpaceAdapter class constructor.

        Returns
        -------
        optimizer : ConcreteOptimizer
            Instance of concrete optimizer class
            (e.g., RandomOptimizer, FlamlOptimizer, SmacOptimizer, etc.).
        """
        if space_adapter_kwargs is None:
            space_adapter_kwargs = {}
        if optimizer_kwargs is None:
            optimizer_kwargs = {}

        space_adapter = SpaceAdapterFactory.create(
            parameter_space=parameter_space,
            space_adapter_type=space_adapter_type,
            space_adapter_kwargs=space_adapter_kwargs,
        )

        optimizer: ConcreteOptimizer = optimizer_type.value(
            parameter_space=parameter_space,
            space_adapter=space_adapter,
            **optimizer_kwargs
        )

        return optimizer

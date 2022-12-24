"""
Basic initializer module for the mlos_core optimizers.
"""

from enum import Enum
from typing import TypeVar

import ConfigSpace
from mlos_core.optimizers.optimizer import BaseOptimizer
from mlos_core.optimizers.random_optimizer import RandomOptimizer
from mlos_core.optimizers.bayesian_optimizers import (
    EmukitOptimizer, SkoptOptimizer)

__all__ = [
    'BaseOptimizer',
    'RandomOptimizer',
    'EmukitOptimizer',
    'SkoptOptimizer',
    'OptimizerFactory',
]


class OptimizerType(Enum):
    """Enumerate supported MlosCore optimizers."""

    RANDOM = RandomOptimizer
    """An instance of RandomOptimizer class will be used"""

    EMUKIT = EmukitOptimizer
    """An instance of EmukitOptimizer class will be used"""

    SKOPT = SkoptOptimizer
    """An instance of SkoptOptimizer class will be used"""


ConcreteOptimizer = TypeVar('ConcreteOptimizer', *[member.value for member in OptimizerType])


class OptimizerFactory:
    """Simple factory class for creating BaseOptimizer-derived objects"""

    @staticmethod
    def create(
        parameter_space: ConfigSpace.ConfigurationSpace,
        optimizer_type: OptimizerType = OptimizerType.SKOPT,
        **kwargs
    ) -> ConcreteOptimizer:
        """Creates a new optimizer instance, given the parameter space, optimizer type and potential optimizer options.

        Parameters
        ----------
        parameter_space : ConfigSpace.ConfigurationSpace
            Input configuration space.

        optimizer_type : OptimizerType
            Optimizer class as defined by Enum.

        **kwargs
            Optional arguments passed in Optimizer class constructor.

        Returns
        -------
        Instance of concrete optimizer (e.g., RandomOptimizer, EmukitOptimizer, SkoptOptimizer, etc.) class.
        """
        return optimizer_type.value(parameter_space, **kwargs)

#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Initializer module for the mlos_core optimizers.

Optimizers are the main component of the :py:mod:`mlos_core` package.
They act as a wrapper around other OSS tuning libraries to provide a consistent API
interface to allow experimenting with different autotuning algorithms.

The :class:`~mlos_core.optimizers.optimizer.BaseOptimizer` class is the base class
for all Optimizers and provides the core
:py:meth:`~mlos_core.optimizers.optimizer.BaseOptimizer.suggest` and
:py:meth:`~mlos_core.optimizers.optimizer.BaseOptimizer.register` methods.

This module also provides a simple :py:class:`~.OptimizerFactory` class to
:py:meth:`~.OptimizerFactory.create` an Optimizer.

Examples
--------
TODO: Add example usage here.

Notes
-----
See `mlos_core/optimizers/README.md
<https://github.com/microsoft/MLOS/tree/main/mlos_core/mlos_core/optimizers/>`_
for additional documentation and examples in the source tree.
"""

from enum import Enum
from typing import TypeVar

import ConfigSpace

from mlos_core.optimizers.bayesian_optimizers.smac_optimizer import SmacOptimizer
from mlos_core.optimizers.flaml_optimizer import FlamlOptimizer
from mlos_core.optimizers.optimizer import BaseOptimizer
from mlos_core.optimizers.random_optimizer import RandomOptimizer
from mlos_core.spaces.adapters import SpaceAdapterFactory, SpaceAdapterType

__all__ = [
    "OptimizerType",
    "ConcreteOptimizer",
    "SpaceAdapterType",
    "OptimizerFactory",
    "BaseOptimizer",
    "RandomOptimizer",
    "FlamlOptimizer",
    "SmacOptimizer",
]


class OptimizerType(Enum):
    """Enumerate supported mlos_core optimizers."""

    RANDOM = RandomOptimizer
    """An instance of :class:`~mlos_core.optimizers.random_optimizer.RandomOptimizer`
    class will be used.
    """

    FLAML = FlamlOptimizer
    """An instance of :class:`~mlos_core.optimizers.flaml_optimizer.FlamlOptimizer`
    class will be used.
    """

    SMAC = SmacOptimizer
    """An instance of
    :class:`~mlos_core.optimizers.bayesian_optimizers.smac_optimizer.SmacOptimizer`
    class will be used.
    """


# To make mypy happy, we need to define a type variable for each optimizer type.
# https://github.com/python/mypy/issues/12952
# ConcreteOptimizer = TypeVar('ConcreteOptimizer', *[member.value for member in OptimizerType])
# To address this, we add a test for complete coverage of the enum.

ConcreteOptimizer = TypeVar(
    "ConcreteOptimizer",
    RandomOptimizer,
    FlamlOptimizer,
    SmacOptimizer,
)
"""
Type variable for concrete optimizer classes.

(e.g., :class:`~mlos_core.optimizers.bayesian_optimizers.smac_optimizer.SmacOptimizer`, etc.)
"""

DEFAULT_OPTIMIZER_TYPE = OptimizerType.FLAML
"""Default optimizer type to use if none is specified."""


class OptimizerFactory:
    """Simple factory class for creating
    :class:`~mlos_core.optimizers.optimizer.BaseOptimizer`-derived objects.
    """

    # pylint: disable=too-few-public-methods

    @staticmethod
    def create(  # pylint: disable=too-many-arguments
        *,
        parameter_space: ConfigSpace.ConfigurationSpace,
        optimization_targets: list[str],
        optimizer_type: OptimizerType = DEFAULT_OPTIMIZER_TYPE,
        optimizer_kwargs: dict | None = None,
        space_adapter_type: SpaceAdapterType = SpaceAdapterType.IDENTITY,
        space_adapter_kwargs: dict | None = None,
    ) -> ConcreteOptimizer:  # type: ignore[type-var]
        """
        Create a new optimizer instance, given the parameter space, optimizer type, and
        potential optimizer options.

        Parameters
        ----------
        parameter_space : ConfigSpace.ConfigurationSpace
            Input configuration space.
        optimization_targets : list[str]
            The names of the optimization targets to minimize.
        optimizer_type : OptimizerType
            Optimizer class as defined by Enum.
        optimizer_kwargs : dict | None
            Optional arguments passed in Optimizer class constructor.
        space_adapter_type : SpaceAdapterType | None
            Space adapter class to be used alongside the optimizer.
        space_adapter_kwargs : dict | None
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
            optimization_targets=optimization_targets,
            space_adapter=space_adapter,
            **optimizer_kwargs,
        )

        return optimizer

#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Contains the BaseSpaceAdapter abstract class.

As mentioned in :py:mod:`mlos_core.spaces.adapters`, the space adapters provide a
mechanism for automatic transformation of the original
:py:class:`ConfigSpace.ConfigurationSpace` provided to the Optimizer into a new
space for the Optimizer to search over.

It's main APIs are the :py:meth:`~.BaseSpaceAdapter.transform` and
:py:meth:`~.BaseSpaceAdapter.inverse_transform` methods, which are used to translate
configurations from one space to another.
"""

from abc import ABCMeta, abstractmethod

import ConfigSpace
import pandas as pd


class BaseSpaceAdapter(metaclass=ABCMeta):
    """
    SpaceAdapter abstract class defining the basic interface.

    Parameters
    ----------
    orig_parameter_space : ConfigSpace.ConfigurationSpace
        The original parameter space to explore.
    """

    def __init__(self, *, orig_parameter_space: ConfigSpace.ConfigurationSpace):
        self._orig_parameter_space: ConfigSpace.ConfigurationSpace = orig_parameter_space
        self._random_state = orig_parameter_space.random

    def __repr__(self) -> str:
        # pylint: disable=consider-using-f-string
        return "{}(original_parameter_space={}, target_parameter_space={})".format(
            self.__class__.__name__,
            self.orig_parameter_space,
            self.target_parameter_space,
        )

    @property
    def orig_parameter_space(self) -> ConfigSpace.ConfigurationSpace:
        """Original (user-provided) parameter space to explore."""
        return self._orig_parameter_space

    @property
    @abstractmethod
    def target_parameter_space(self) -> ConfigSpace.ConfigurationSpace:
        """Target parameter space that is fed to the underlying optimizer."""
        pass  # pylint: disable=unnecessary-pass # pragma: no cover

    @abstractmethod
    def transform(self, configuration: pd.Series) -> pd.Series:
        """
        Translates a configuration, which belongs to the target parameter space, to the
        original parameter space. This method is called by the
        :py:meth:`~mlos_core.optimizers.optimizer.BaseOptimizer.suggest` method of the
        :py:class:`~mlos_core.optimizers.optimizer.BaseOptimizer` class.

        Parameters
        ----------
        configuration : pandas.Series
            Pandas series. Column names are the parameter names
            of the target parameter space.

        Returns
        -------
        configuration : pandas.Series
            Pandas series, containing the translated configuration.
            Column names are the parameter names of the original parameter space.
        """
        pass  # pylint: disable=unnecessary-pass # pragma: no cover

    @abstractmethod
    def inverse_transform(self, configuration: pd.Series) -> pd.Series:
        """
        Translates a configuration, which belongs to the original parameter space, to
        the target parameter space. This method is called by the `register` method of
        the :py:class:`~mlos_core.optimizers.optimizer.BaseOptimizer` class, and
        performs the inverse operation of :py:meth:`~.BaseSpaceAdapter.transform`
        method.

        Parameters
        ----------
        configuration : pandas.Series
            A Series of configuration parameters, which belong to the original parameter space.
            The indices are the parameter names the original parameter space and the
            rows are the configurations.

        Returns
        -------
        configuration : pandas.Series
            Series of the translated configurations / parameters.
            The indices are the parameter names of the target parameter space and
            the rows are the configurations.
        """
        pass  # pylint: disable=unnecessary-pass # pragma: no cover

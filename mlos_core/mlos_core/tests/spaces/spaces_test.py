#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Tests for mlos_core.spaces
"""

# pylint: disable=missing-function-docstring

from abc import ABCMeta, abstractmethod
from typing import Any, Callable, List, NoReturn, Union

import numpy as np
import numpy.typing as npt
import pytest

import scipy
import emukit.core

import ConfigSpace as CS
from ConfigSpace.hyperparameters import NormalIntegerHyperparameter

from mlos_core.spaces import configspace_to_emukit_space


# NOTE: Originally this was a union of emukit and skopt supported space/param
# types, but since we removed skopt support the union needs to have another
# element in it, so we list the original input type again for now (technically
# true for SMAC, for instance).
OptimizerSpace = Union[emukit.core.ParameterSpace, CS.ConfigurationSpace]
OptimizerParam = Union[emukit.core.Parameter, CS.hyperparameters.Hyperparameter]


def assert_uniform_counts(counts: npt.NDArray) -> None:
    _chi_sq, p_value = scipy.stats.chisquare(counts)
    assert p_value > .3


def invalid_conversion_function(*args: Any) -> NoReturn:
    """
    A quick dummy function for the base class to make pylint happy.
    """
    raise NotImplementedError('subclass must override conversion_function')


class BaseConversion(metaclass=ABCMeta):
    """
    Base class for testing optimizer space conversions.
    """
    conversion_function: Callable[..., OptimizerSpace] = invalid_conversion_function

    @abstractmethod
    def sample(self, config_space: OptimizerSpace, n_samples: int = 1) -> OptimizerParam:
        """
        Sample from the given configuration space.

        Parameters
        ----------
        config_space : CS.ConfigurationSpace
            Configuration space to sample from.
        n_samples : int, optional
            Number of samples to use, by default 1.
        """

    @abstractmethod
    def get_parameter_names(self, config_space: OptimizerSpace) -> List[str]:
        """
        Get the parameter names from the given configuration space.

        Parameters
        ----------
        config_space : CS.ConfigurationSpace
            Configuration space.
        """

    @abstractmethod
    def categorical_counts(self, points: npt.NDArray) -> npt.NDArray:
        """
        Get the counts of each categorical value in the given points.

        Parameters
        ----------
        points : np.array
            Counts of each categorical value.
        """

    @abstractmethod
    def test_dimensionality(self) -> None:
        """
        Check that the dimensionality of the converted space is correct.
        """

    def test_unsupported_hyperparameter(self) -> None:
        input_space = CS.ConfigurationSpace()
        input_space.add_hyperparameter(NormalIntegerHyperparameter("a", 2, 1))
        with pytest.raises(ValueError, match="NormalIntegerHyperparameter"):
            self.conversion_function(input_space)

    def test_continuous_bounds(self) -> None:
        input_space = CS.ConfigurationSpace()
        input_space.add_hyperparameter(CS.UniformFloatHyperparameter("a", lower=100, upper=200))
        input_space.add_hyperparameter(CS.UniformIntegerHyperparameter("b", lower=-10, upper=-5))

        converted_space = self.conversion_function(input_space)
        assert self.get_parameter_names(converted_space) == ["a", "b"]
        point, *_ = self.sample(converted_space)
        assert 100 <= point[0] <= 200
        assert -10 <= point[1] <= -5

    def test_uniform_samples(self) -> None:
        input_space = CS.ConfigurationSpace()
        input_space.add_hyperparameter(CS.UniformFloatHyperparameter("a", lower=1, upper=5))
        input_space.add_hyperparameter(CS.UniformIntegerHyperparameter("c", lower=1, upper=20))
        converted_space = self.conversion_function(input_space)

        np.random.seed(42)
        uniform, integer_uniform = self.sample(converted_space, n_samples=1000).T

        # uniform float
        counts, _ = np.histogram(uniform, bins='auto')
        assert_uniform_counts(counts)
        # integer uniform
        integer_uniform = np.array(integer_uniform)
        # bincount always starts from zero
        integer_uniform = integer_uniform - integer_uniform.min()
        assert_uniform_counts(np.bincount(integer_uniform.astype(int)))

    def test_uniform_categorical(self) -> None:
        input_space = CS.ConfigurationSpace()
        input_space.add_hyperparameter(CS.CategoricalHyperparameter("c", choices=["foo", "bar"]))
        converted_space = self.conversion_function(input_space)
        points = self.sample(converted_space, n_samples=100)
        counts = self.categorical_counts(points)
        assert 35 < counts[0] < 65
        assert 35 < counts[1] < 65

    def test_weighted_categorical(self) -> None:
        raise NotImplementedError('subclass must override')

    def test_log_spaces(self) -> None:
        raise NotImplementedError('subclass must override')


class TestEmukitConversion(BaseConversion):
    """
    Tests for ConfigSpace to Emukit parameter conversions.
    """

    conversion_function = staticmethod(configspace_to_emukit_space)

    # Note: these types are currently correct via manual inspection of the
    # emukit code, however since emukit doesn't py.typed mark itself yet mypy
    # can't introspect them correctly.

    def sample(self, config_space: emukit.core.ParameterSpace, n_samples: int = 1) -> npt.NDArray:
        ret: npt.NDArray = config_space.sample_uniform(point_count=n_samples)
        return ret

    def get_parameter_names(self, config_space: emukit.core.ParameterSpace) -> List[str]:
        ret: List[str] = config_space.parameter_names
        return ret

    def categorical_counts(self, points: npt.NDArray) -> npt.NDArray:
        ret: npt.NDArray = np.sum(points, axis=0)
        return ret

    def test_dimensionality(self) -> None:
        input_space = CS.ConfigurationSpace()
        input_space.add_hyperparameter(CS.UniformIntegerHyperparameter("a", lower=1, upper=10))
        input_space.add_hyperparameter(CS.CategoricalHyperparameter("b", choices=["bof", "bum"]))
        input_space.add_hyperparameter(CS.CategoricalHyperparameter("c", choices=["foo", "bar"]))
        output_space = configspace_to_emukit_space(input_space)
        # NOTE: categorical params get expanded to multiple dimensions in the
        # hyperparameter space for emukit when OneHotEncoding is used.
        assert output_space.dimensionality == 5

    def test_weighted_categorical(self) -> None:
        np.random.seed(42)
        input_space = CS.ConfigurationSpace()
        input_space.add_hyperparameter(CS.CategoricalHyperparameter("c", choices=["foo", "bar"], weights=[0.9, 0.1]))
        with pytest.raises(ValueError, match="non-uniform"):
            configspace_to_emukit_space(input_space)

    def test_log_spaces(self) -> None:
        # continuous not supported
        input_space = CS.ConfigurationSpace()
        input_space.add_hyperparameter(CS.UniformFloatHyperparameter("b", lower=1, upper=5, log=True))
        with pytest.raises(ValueError, match="log"):
            configspace_to_emukit_space(input_space)
        # integer is supported
        input_space = CS.ConfigurationSpace()
        input_space.add_hyperparameter(CS.UniformIntegerHyperparameter("d", lower=1, upper=20, log=True))
        converted_space = configspace_to_emukit_space(input_space)

        np.random.seed(42)

        integer_log_uniform = converted_space.sample_uniform(point_count=1000)

        # log integer
        integer_log_uniform = np.array(integer_log_uniform).ravel()
        logs = np.log(integer_log_uniform)
        int_logs = logs.round().astype(np.int64)
        diffs = logs - int_logs
        assert np.allclose(diffs, 0)
        bincounts = np.bincount(int_logs)
        assert_uniform_counts(bincounts)

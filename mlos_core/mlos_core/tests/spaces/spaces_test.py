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

import ConfigSpace as CS
from ConfigSpace.hyperparameters import NormalIntegerHyperparameter

import flaml.tune.sample

from mlos_core.spaces.converters.flaml import configspace_to_flaml_space, FlamlDomain, FlamlSpace


OptimizerSpace = Union[FlamlSpace, CS.ConfigurationSpace]
OptimizerParam = Union[FlamlDomain, CS.hyperparameters.Hyperparameter]


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

    def test_log_int_spaces(self) -> None:
        raise NotImplementedError('subclass must override')

    def test_log_float_spaces(self) -> None:
        raise NotImplementedError('subclass must override')


class TestFlamlConversion(BaseConversion):
    """
    Tests for ConfigSpace to Flaml parameter conversions.
    """

    conversion_function = staticmethod(configspace_to_flaml_space)

    def sample(self, config_space: FlamlSpace, n_samples: int = 1) -> npt.NDArray:  # type: ignore[override]
        assert isinstance(config_space, dict)
        assert isinstance(next(iter(config_space.values())), flaml.tune.sample.Domain)
        ret: npt.NDArray = np.array([domain.sample(size=n_samples) for domain in config_space.values()]).T
        return ret

    def get_parameter_names(self, config_space: FlamlSpace) -> List[str]:   # type: ignore[override]
        assert isinstance(config_space, dict)
        ret: List[str] = list(config_space.keys())
        return ret

    def categorical_counts(self, points: npt.NDArray) -> npt.NDArray:
        _vals, counts = np.unique(points, return_counts=True)
        assert isinstance(counts, np.ndarray)
        return counts

    def test_dimensionality(self) -> None:
        input_space = CS.ConfigurationSpace()
        input_space.add_hyperparameter(CS.UniformIntegerHyperparameter("a", lower=1, upper=10))
        input_space.add_hyperparameter(CS.CategoricalHyperparameter("b", choices=["bof", "bum"]))
        input_space.add_hyperparameter(CS.CategoricalHyperparameter("c", choices=["foo", "bar"]))
        output_space = configspace_to_flaml_space(input_space)
        assert len(output_space) == 3

    def test_weighted_categorical(self) -> None:
        np.random.seed(42)
        input_space = CS.ConfigurationSpace()
        input_space.add_hyperparameter(CS.CategoricalHyperparameter("c", choices=["foo", "bar"], weights=[0.9, 0.1]))
        with pytest.raises(ValueError, match="non-uniform"):
            configspace_to_flaml_space(input_space)

    def test_log_int_spaces(self) -> None:
        np.random.seed(42)

        # integer is supported
        input_space = CS.ConfigurationSpace()
        input_space.add_hyperparameter(CS.UniformIntegerHyperparameter("d", lower=1, upper=20, log=True))
        converted_space = configspace_to_flaml_space(input_space)

        integer_log_uniform = self.sample(converted_space, n_samples=1000)

        # log integer
        integer_log_uniform = np.array(integer_log_uniform).ravel()
        logs = np.log(integer_log_uniform)

        raise NotImplementedError('TODO: test int log uniform')

    def test_log_float_spaces(self) -> None:
        np.random.seed(42)

        # continuous is supported
        input_space = CS.ConfigurationSpace()
        input_space.add_hyperparameter(CS.UniformFloatHyperparameter("b", lower=1, upper=5, log=True))
        converted_space = configspace_to_flaml_space(input_space)

        # TODO: test float log uniform
        float_log_uniform = self.sample(converted_space, n_samples=1000)
        float_log_uniform = np.array(float_log_uniform).ravel()
        logs = np.log(float_log_uniform)

        raise NotImplementedError('TODO: test float log uniform')

#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Tests for mlos_core.spaces."""

# pylint: disable=missing-function-docstring

from abc import ABCMeta, abstractmethod
from typing import Any, Callable, List, NoReturn, Union

import ConfigSpace as CS
import flaml.tune.sample
import numpy as np
import numpy.typing as npt
import pytest
import scipy
from ConfigSpace.hyperparameters import Hyperparameter, NormalIntegerHyperparameter

from mlos_core.spaces.converters.flaml import (
    FlamlDomain,
    FlamlSpace,
    configspace_to_flaml_space,
)

OptimizerSpace = Union[FlamlSpace, CS.ConfigurationSpace]
OptimizerParam = Union[FlamlDomain, Hyperparameter]


def assert_is_uniform(arr: npt.NDArray) -> None:
    """Implements a few tests for uniformity."""
    _values, counts = np.unique(arr, return_counts=True)

    kurtosis = scipy.stats.kurtosis(arr)

    _chi_sq, p_value = scipy.stats.chisquare(counts)

    frequencies = counts / len(arr)
    assert np.isclose(frequencies.sum(), 1)
    _f_chi_sq, f_p_value = scipy.stats.chisquare(frequencies)

    assert np.isclose(kurtosis, -1.2, atol=0.1)
    assert p_value > 0.3
    assert f_p_value > 0.5


def assert_is_log_uniform(arr: npt.NDArray, base: float = np.e) -> None:
    """Checks whether an array is log uniformly distributed."""
    logs = np.log(arr) / np.log(base)
    assert_is_uniform(logs)


def test_is_uniform() -> None:
    """Test our uniform distribution check function."""
    np.random.seed(42)
    uniform = np.random.uniform(1, 20, 1000)
    assert_is_uniform(uniform)


def test_is_log_uniform() -> None:
    """Test our log uniform distribution check function."""
    np.random.seed(42)
    log_uniform = np.exp(np.random.uniform(np.log(1), np.log(20), 1000))
    assert_is_log_uniform(log_uniform)


def invalid_conversion_function(*args: Any) -> NoReturn:
    """A quick dummy function for the base class to make pylint happy."""
    raise NotImplementedError("subclass must override conversion_function")


class BaseConversion(metaclass=ABCMeta):
    """Base class for testing optimizer space conversions."""

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
        """Check that the dimensionality of the converted space is correct."""

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
        point = self.sample(converted_space)
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
        assert_is_uniform(uniform)

        # Check that we get both ends of the sampled range returned to us.
        assert input_space["c"].lower in integer_uniform
        assert input_space["c"].upper in integer_uniform
        # integer uniform
        assert_is_uniform(integer_uniform)

    def test_uniform_categorical(self) -> None:
        input_space = CS.ConfigurationSpace()
        input_space.add_hyperparameter(CS.CategoricalHyperparameter("c", choices=["foo", "bar"]))
        converted_space = self.conversion_function(input_space)
        points = self.sample(converted_space, n_samples=100)
        counts = self.categorical_counts(points)
        assert 35 < counts[0] < 65
        assert 35 < counts[1] < 65

    def test_weighted_categorical(self) -> None:
        raise NotImplementedError("subclass must override")

    def test_log_int_spaces(self) -> None:
        raise NotImplementedError("subclass must override")

    def test_log_float_spaces(self) -> None:
        raise NotImplementedError("subclass must override")


class TestFlamlConversion(BaseConversion):
    """Tests for ConfigSpace to Flaml parameter conversions."""

    conversion_function = staticmethod(configspace_to_flaml_space)

    def sample(
        self,
        config_space: FlamlSpace,  # type: ignore[override]
        n_samples: int = 1,
    ) -> npt.NDArray:
        assert isinstance(config_space, dict)
        assert isinstance(next(iter(config_space.values())), flaml.tune.sample.Domain)
        ret: npt.NDArray = np.array(
            [domain.sample(size=n_samples) for domain in config_space.values()]
        ).T
        return ret

    def get_parameter_names(self, config_space: FlamlSpace) -> List[str]:  # type: ignore[override]
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
        input_space.add_hyperparameter(
            CS.CategoricalHyperparameter("c", choices=["foo", "bar"], weights=[0.9, 0.1])
        )
        with pytest.raises(ValueError, match="non-uniform"):
            configspace_to_flaml_space(input_space)

    @pytest.mark.skip(reason="FIXME: flaml sampling is non-log-uniform")
    def test_log_int_spaces(self) -> None:
        np.random.seed(42)
        # integer is supported
        input_space = CS.ConfigurationSpace()
        input_space.add_hyperparameter(
            CS.UniformIntegerHyperparameter("d", lower=1, upper=20, log=True)
        )
        converted_space = configspace_to_flaml_space(input_space)

        # test log integer sampling
        integer_log_uniform = self.sample(converted_space, n_samples=1000)
        integer_log_uniform = np.array(integer_log_uniform).ravel()

        # FIXME: this fails - flaml is calling np.random.uniform() on base 10
        # logs of the bounds as expected but for some reason the resulting
        # samples are more skewed towards the lower end of the range
        # See Also: https://github.com/microsoft/FLAML/issues/1104
        assert_is_log_uniform(integer_log_uniform, base=10)

    def test_log_float_spaces(self) -> None:
        np.random.seed(42)

        # continuous is supported
        input_space = CS.ConfigurationSpace()
        input_space.add_hyperparameter(
            CS.UniformFloatHyperparameter("b", lower=1, upper=5, log=True)
        )
        converted_space = configspace_to_flaml_space(input_space)

        # test log integer sampling
        float_log_uniform = self.sample(converted_space, n_samples=1000)
        float_log_uniform = np.array(float_log_uniform).ravel()

        assert_is_log_uniform(float_log_uniform)


if __name__ == "__main__":
    # For attaching debugger debugging:
    pytest.main(["-vv", "-k", "test_log_int_spaces", __file__])

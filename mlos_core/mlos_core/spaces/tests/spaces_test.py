import numpy as np
import pandas as pd
import pytest
import scipy

import ConfigSpace as CS
from ConfigSpace.hyperparameters import NormalIntegerHyperparameter
from mlos_core.spaces import configspace_to_emukit_space, configspace_to_skopt_space


def assert_uniform_counts(counts):
    _, p = scipy.stats.chisquare(counts)
    assert p > .3


class BaseConversion:
    conversion_function = None

    def sample(self, config_space, n_samples=1):
        raise NotImplementedError

    def get_parameter_names(self, config_space):
        raise NotImplementedError

    def test_unsupported_hyperparameter(self):
        input_space = CS.ConfigurationSpace()
        input_space.add_hyperparameter(NormalIntegerHyperparameter("a", 2, 1))
        with pytest.raises(ValueError, match="NormalIntegerHyperparameter"):
            self.conversion_function(input_space)

    def test_continuous_bounds(self):
        input_space = CS.ConfigurationSpace()
        input_space.add_hyperparameter(CS.UniformFloatHyperparameter("a", lower=100, upper=200))
        input_space.add_hyperparameter(CS.UniformIntegerHyperparameter("b", lower=-10, upper=-5))

        converted_space = self.conversion_function(input_space)
        assert self.get_parameter_names(converted_space) == ["a", "b"]
        point, = self.sample(converted_space)
        assert 100 <= point[0] <= 200
        assert -10 <= point[1] <= -5

    def test_uniform_samples(self):
        input_space = CS.ConfigurationSpace()
        input_space.add_hyperparameter(CS.UniformFloatHyperparameter("a", lower=1, upper=5))
        input_space.add_hyperparameter(CS.UniformIntegerHyperparameter("c", lower=1, upper=20))
        converted_space = self.conversion_function(input_space)

        np.random.seed(42)
        uniform, integer_uniform = self.sample(converted_space, n_samples=1000).T

        # uniform flaot
        counts, _ = np.histogram(uniform, bins='auto')
        assert_uniform_counts(counts)
        # integer uniform
        integer_uniform = np.array(integer_uniform)
        # bincount always starts from zero
        integer_uniform = integer_uniform - integer_uniform.min()
        assert_uniform_counts(np.bincount(integer_uniform.astype(int)))

    def test_uniform_categorical(self):
        input_space = CS.ConfigurationSpace()
        input_space.add_hyperparameter(CS.CategoricalHyperparameter("c", choices=["foo", "bar"]))
        converted_space = self.conversion_function(input_space)
        points = self.sample(converted_space, n_samples=100)
        counts = self.categorical_counts(points)
        assert 35 < counts[0] < 65
        assert 35 < counts[1] < 65

    def test_weighted_categorical(self):
        raise NotImplementedError

    def test_log_spaces(self):
        raise NotImplementedError


class TestSkoptConversion(BaseConversion):
    conversion_function = staticmethod(configspace_to_skopt_space)

    def sample(self, config_space, n_samples=1):
        return np.array(config_space.rvs(n_samples=n_samples))

    def get_parameter_names(self, config_space):
        return config_space.dimension_names

    def categorical_counts(self, points):
        return pd.value_counts(points[:, 0]).values

    def test_weighted_categorical(self):
        input_space = CS.ConfigurationSpace()
        input_space.add_hyperparameter(CS.CategoricalHyperparameter("c", choices=["foo", "bar"], weights=[0.9, 0.1]))
        # unpack the space to only get a parameter so we can count more easily later
        converted_space, = configspace_to_skopt_space(input_space)
        random_state = np.random.RandomState(42)
        sample = converted_space.rvs(n_samples=100, random_state=random_state)
        counts = pd.value_counts(sample)
        assert counts["foo"] > 80
        assert counts["bar"] > 5

    def test_log_spaces(self):
        input_space = CS.ConfigurationSpace()
        input_space.add_hyperparameter(CS.UniformFloatHyperparameter("b", lower=1, upper=5, log=True))
        input_space.add_hyperparameter(CS.UniformIntegerHyperparameter("d", lower=1, upper=20, log=True))
        converted_space = configspace_to_skopt_space(input_space)

        random_state = np.random.RandomState(42)
        log_uniform, integer_log_uniform = zip(
            *converted_space.rvs(n_samples=1000, random_state=random_state))

        # log uniform float
        counts, _ = np.histogram(np.log(log_uniform), bins='auto')
        assert_uniform_counts(counts)
        # log integer
        integer_log_uniform = np.array(integer_log_uniform)
        integer_log_uniform = integer_log_uniform - integer_log_uniform.min()
        # TODO double check the math on this
        assert_uniform_counts(np.log(np.bincount(integer_log_uniform)))


class TestEmukitConversion(BaseConversion):
    conversion_function = staticmethod(configspace_to_emukit_space)

    def sample(self, config_space, n_samples=1):
        return config_space.sample_uniform(point_count=n_samples)

    def get_parameter_names(self, config_space):
        return config_space.parameter_names

    def categorical_counts(self, points):
        return np.sum(points, axis=0)

    def test_weighted_categorical(self):
        np.random.seed(42)
        input_space = CS.ConfigurationSpace()
        input_space.add_hyperparameter(CS.CategoricalHyperparameter("c", choices=["foo", "bar"], weights=[0.9, 0.1]))
        with pytest.raises(ValueError, match="non-uniform"):
            configspace_to_emukit_space(input_space)

    def test_log_spaces(self):
        # continuous not supported
        input_space = CS.ConfigurationSpace()
        input_space.add_hyperparameter(CS.UniformFloatHyperparameter("b", lower=1, upper=5, log=True))
        with pytest.raises(ValueError, match="log"):
            configspace_to_emukit_space(input_space)
        # integer is supported
        input_space = CS.ConfigurationSpace()
        input_space.add_hyperparameter(CS.UniformIntegerHyperparameter("d", lower=1, upper=20, log=True))
        converted_space = configspace_to_skopt_space(input_space)

        random_state = np.random.RandomState(42)
        integer_log_uniform = converted_space.rvs(n_samples=1000, random_state=random_state)

        # log integer
        integer_log_uniform = np.array(integer_log_uniform).ravel()
        integer_log_uniform = integer_log_uniform - integer_log_uniform.min()
        # TODO double check the math on this
        assert_uniform_counts(np.log(np.bincount(integer_log_uniform)))
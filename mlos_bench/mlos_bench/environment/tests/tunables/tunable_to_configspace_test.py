"""
Unit tests for Tunable to ConfigSpace conversion.
"""

from ConfigSpace import UniformIntegerHyperparameter
from ConfigSpace import UniformFloatHyperparameter
from ConfigSpace import CategoricalHyperparameter

from mlos_bench.environment import Tunable, TunableGroups
from mlos_bench.convert_configspace import _tunable_to_hyperparameter
from mlos_bench.convert_configspace import tunable_groups_to_configspace

# pylint: disable=protected-access


def _cmp_tunable_hyperparameter_categorical(
        tunable: Tunable, cs_param: CategoricalHyperparameter):
    """
    Check if categorical Tunable and ConfigSpace Hyperparameter actually match.
    """
    assert isinstance(cs_param, CategoricalHyperparameter)
    assert set(cs_param.choices) == set(tunable._values)
    assert cs_param.default_value == tunable.value


def _cmp_tunable_hyperparameter_int(
        tunable: Tunable, cs_param: UniformIntegerHyperparameter):
    """
    Check if integer Tunable and ConfigSpace Hyperparameter actually match.
    """
    assert isinstance(cs_param, UniformIntegerHyperparameter)
    assert (cs_param.lower, cs_param.upper) == tuple(tunable._range)
    assert cs_param.default_value == tunable.value


def _cmp_tunable_hyperparameter_float(
        tunable: Tunable, cs_param: UniformFloatHyperparameter):
    """
    Check if float Tunable and ConfigSpace Hyperparameter actually match.
    """
    assert isinstance(cs_param, UniformFloatHyperparameter)
    assert (cs_param.lower, cs_param.upper) == tuple(tunable._range)
    assert cs_param.default_value == tunable.value


def test_tunable_to_hyperparameter_categorical(tunable_categorical):
    """
    Check the conversion of Tunable to CategoricalHyperparameter.
    """
    cs_param = _tunable_to_hyperparameter(tunable_categorical)
    _cmp_tunable_hyperparameter_categorical(tunable_categorical, cs_param)


def test_tunable_to_hyperparameter_int(tunable_int):
    """
    Check the conversion of Tunable to UniformIntegerHyperparameter.
    """
    cs_param = _tunable_to_hyperparameter(tunable_int)
    _cmp_tunable_hyperparameter_int(tunable_int, cs_param)


def test_tunable_to_hyperparameter_float(tunable_float):
    """
    Check the conversion of Tunable to UniformFloatHyperparameter.
    """
    cs_param = _tunable_to_hyperparameter(tunable_float)
    _cmp_tunable_hyperparameter_float(tunable_float, cs_param)


def test_tunable_groups_to_configspace(tunable_groups: TunableGroups):
    """
    Check the conversion of the entire TunableGroups collection
    to a list of ConfigSpace Hyperparameter objects.
    """
    cs_hyperparams = {param.name: param
                      for param in tunable_groups_to_configspace(tunable_groups)}
    for group in tunable_groups._tunable_groups.values():
        for (name, tunable) in group._tunables.items():
            cs_param = cs_hyperparams[name]
            assert cs_param.default_value == tunable.value
            if tunable._type == "int":
                _cmp_tunable_hyperparameter_int(tunable, cs_param)
            elif tunable._type == "float":
                _cmp_tunable_hyperparameter_float(tunable, cs_param)
            elif tunable._type == "categorical":
                _cmp_tunable_hyperparameter_categorical(tunable, cs_param)
            else:
                assert False, "Invalid tunable type"

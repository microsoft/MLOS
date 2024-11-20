#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Tests for Identity space adapter."""

# pylint: disable=missing-function-docstring

import ConfigSpace as CS
import pandas as pd

from mlos_core.spaces.adapters import IdentityAdapter


def test_identity_adapter() -> None:
    """Tests identity adapter."""
    input_space = CS.ConfigurationSpace(seed=1234)
    input_space.add(CS.UniformIntegerHyperparameter(name="int_1", lower=0, upper=100))
    input_space.add(CS.UniformFloatHyperparameter(name="float_1", lower=0, upper=100))
    input_space.add(CS.CategoricalHyperparameter(name="str_1", choices=["on", "off"]))

    adapter = IdentityAdapter(orig_parameter_space=input_space)

    num_configs = 10
    for sampled_config in input_space.sample_configuration(
        size=num_configs
    ):  # pylint: disable=not-an-iterable # (false positive)
        sampled_config_sr = pd.Series(dict(sampled_config))
        target_config_sr = adapter.inverse_transform(sampled_config_sr)
        assert target_config_sr.equals(sampled_config_sr)
        target_config = CS.Configuration(
            adapter.target_parameter_space, values=target_config_sr.to_dict()
        )
        assert target_config == sampled_config
        orig_config_df = adapter.transform(target_config_sr)
        assert orig_config_df.equals(sampled_config_sr)
        orig_config = CS.Configuration(
            adapter.orig_parameter_space, values=orig_config_df.to_dict()
        )
        assert orig_config == sampled_config

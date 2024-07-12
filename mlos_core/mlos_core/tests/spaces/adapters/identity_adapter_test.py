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
    input_space.add_hyperparameter(
        CS.UniformIntegerHyperparameter(name="int_1", lower=0, upper=100)
    )
    input_space.add_hyperparameter(
        CS.UniformFloatHyperparameter(name="float_1", lower=0, upper=100)
    )
    input_space.add_hyperparameter(
        CS.CategoricalHyperparameter(name="str_1", choices=["on", "off"])
    )

    adapter = IdentityAdapter(orig_parameter_space=input_space)

    num_configs = 10
    for sampled_config in input_space.sample_configuration(
        size=num_configs
    ):  # pylint: disable=not-an-iterable # (false positive)
        sampled_config_df = pd.DataFrame(
            [sampled_config.values()], columns=list(sampled_config.keys())
        )
        target_config_df = adapter.inverse_transform(sampled_config_df)
        assert target_config_df.equals(sampled_config_df)
        target_config = CS.Configuration(
            adapter.target_parameter_space, values=target_config_df.iloc[0].to_dict()
        )
        assert target_config == sampled_config
        orig_config_df = adapter.transform(target_config_df)
        assert orig_config_df.equals(sampled_config_df)
        orig_config = CS.Configuration(
            adapter.orig_parameter_space, values=orig_config_df.iloc[0].to_dict()
        )
        assert orig_config == sampled_config

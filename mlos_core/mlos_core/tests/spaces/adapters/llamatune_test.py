#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Tests for LlamaTune space adapter."""

# pylint: disable=missing-function-docstring

from typing import Any, Dict, Iterator, List, Set

import ConfigSpace as CS
import pandas as pd
import pytest

from mlos_core.spaces.adapters import LlamaTuneAdapter


def construct_parameter_space(
    n_continuous_params: int = 0,
    n_integer_params: int = 0,
    n_categorical_params: int = 0,
    seed: int = 1234,
) -> CS.ConfigurationSpace:
    """Helper function for construct an instance of `ConfigSpace.ConfigurationSpace`."""
    input_space = CS.ConfigurationSpace(seed=seed)

    for idx in range(n_continuous_params):
        input_space.add_hyperparameter(
            CS.UniformFloatHyperparameter(name=f"cont_{idx}", lower=0, upper=64)
        )
    for idx in range(n_integer_params):
        input_space.add_hyperparameter(
            CS.UniformIntegerHyperparameter(name=f"int_{idx}", lower=-1, upper=256)
        )
    for idx in range(n_categorical_params):
        input_space.add_hyperparameter(
            CS.CategoricalHyperparameter(
                name=f"str_{idx}", choices=[f"option_{idx}" for idx in range(5)]
            )
        )

    return input_space


@pytest.mark.parametrize(
    ("num_target_space_dims", "param_space_kwargs"),
    (
        [
            (num_target_space_dims, param_space_kwargs)
            for num_target_space_dims in (2, 4)
            for num_orig_space_factor in (1.5, 4)
            for param_space_kwargs in (
                {"n_continuous_params": int(num_target_space_dims * num_orig_space_factor)},
                {"n_integer_params": int(num_target_space_dims * num_orig_space_factor)},
                {"n_categorical_params": int(num_target_space_dims * num_orig_space_factor)},
                # Mix of all three types
                {
                    "n_continuous_params": int(num_target_space_dims * num_orig_space_factor / 3),
                    "n_integer_params": int(num_target_space_dims * num_orig_space_factor / 3),
                    "n_categorical_params": int(num_target_space_dims * num_orig_space_factor / 3),
                },
            )
        ]
    ),
)
def test_num_low_dims(
    num_target_space_dims: int,
    param_space_kwargs: dict,
) -> None:  # pylint: disable=too-many-locals
    """Tests LlamaTune's low-to-high space projection method."""
    input_space = construct_parameter_space(**param_space_kwargs)

    # Number of target parameter space dimensions should be fewer than those of the original space
    with pytest.raises(ValueError):
        LlamaTuneAdapter(
            orig_parameter_space=input_space, num_low_dims=len(list(input_space.keys()))
        )

    # Enable only low-dimensional space projections
    adapter = LlamaTuneAdapter(
        orig_parameter_space=input_space,
        num_low_dims=num_target_space_dims,
        special_param_values=None,
        max_unique_values_per_param=None,
    )

    sampled_configs = adapter.target_parameter_space.sample_configuration(size=100)
    for sampled_config in sampled_configs:  # pylint: disable=not-an-iterable # (false positive)
        # Transform low-dim config to high-dim point/config
        sampled_config_df = pd.DataFrame(
            [sampled_config.values()], columns=list(sampled_config.keys())
        )
        orig_config_df = adapter.transform(sampled_config_df)

        # High-dim (i.e., original) config should be valid
        orig_config = CS.Configuration(input_space, values=orig_config_df.iloc[0].to_dict())
        input_space.check_configuration(orig_config)

        # Transform high-dim config back to low-dim
        target_config_df = adapter.inverse_transform(orig_config_df)

        # Sampled config and this should be the same
        target_config = CS.Configuration(
            adapter.target_parameter_space,
            values=target_config_df.iloc[0].to_dict(),
        )
        assert target_config == sampled_config

    # Try inverse projection (i.e., high-to-low) for previously unseen configs
    unseen_sampled_configs = adapter.target_parameter_space.sample_configuration(size=25)
    for (
        unseen_sampled_config
    ) in unseen_sampled_configs:  # pylint: disable=not-an-iterable # (false positive)
        if (
            unseen_sampled_config in sampled_configs
        ):  # pylint: disable=unsupported-membership-test # (false positive)
            continue

        unseen_sampled_config_df = pd.DataFrame(
            [unseen_sampled_config.values()], columns=list(unseen_sampled_config.keys())
        )
        with pytest.raises(ValueError):
            _ = adapter.inverse_transform(
                unseen_sampled_config_df
            )  # pylint: disable=redefined-variable-type


def test_special_parameter_values_validation() -> None:
    """Tests LlamaTune's validation process of user-provided special parameter values
    dictionary.
    """
    input_space = CS.ConfigurationSpace(seed=1234)
    input_space.add_hyperparameter(
        CS.CategoricalHyperparameter(name="str", choices=[f"choice_{idx}" for idx in range(5)])
    )
    input_space.add_hyperparameter(CS.UniformFloatHyperparameter(name="cont", lower=-1, upper=100))
    input_space.add_hyperparameter(CS.UniformIntegerHyperparameter(name="int", lower=0, upper=100))

    # Only UniformIntegerHyperparameters are currently supported
    with pytest.raises(NotImplementedError):
        special_param_values_dict_1 = {"str": "choice_1"}
        LlamaTuneAdapter(
            orig_parameter_space=input_space,
            num_low_dims=2,
            special_param_values=special_param_values_dict_1,
            max_unique_values_per_param=None,
        )

    with pytest.raises(NotImplementedError):
        special_param_values_dict_2 = {"cont": -1}
        LlamaTuneAdapter(
            orig_parameter_space=input_space,
            num_low_dims=2,
            special_param_values=special_param_values_dict_2,
            max_unique_values_per_param=None,
        )

    # Special value should belong to parameter value domain
    with pytest.raises(ValueError, match="value domain"):
        special_param_values_dict = {"int": -1}
        LlamaTuneAdapter(
            orig_parameter_space=input_space,
            num_low_dims=2,
            special_param_values=special_param_values_dict,
            max_unique_values_per_param=None,
        )

    # Invalid dicts; ValueError should be thrown
    invalid_special_param_values_dicts: List[Dict[str, Any]] = [
        {"int-Q": 0},  # parameter does not exist
        {"int": {0: 0.2}},  # invalid definition
        {"int": 0.2},  # invalid parameter value
        {"int": (0.4, 0)},  # (biasing %, special value) instead of (special value, biasing %)
        {"int": [0, 0]},  # duplicate special values
        {"int": []},  # empty list
        {"int": [{0: 0.2}]},
        {"int": [(0.4, 0), (1, 0.7)]},  # first tuple is inverted; second is correct
        {"int": [(0, 0.1), (0, 0.2)]},  # duplicate special values
    ]
    for spv_dict in invalid_special_param_values_dicts:
        with pytest.raises(ValueError):
            LlamaTuneAdapter(
                orig_parameter_space=input_space,
                num_low_dims=2,
                special_param_values=spv_dict,
                max_unique_values_per_param=None,
            )

    # Biasing percentage of special value(s) are invalid
    invalid_special_param_values_dicts = [
        {"int": (0, 1.1)},  # >1 probability
        {"int": (0, 0)},  # Zero probability
        {"int": (0, -0.1)},  # Negative probability
        {"int": (0, 20)},  # 2,000% instead of 20%
        {"int": [0, 1, 2, 3, 4, 5]},  # default biasing is 20%; 6 values * 20% > 100%
        {"int": [(0, 0.4), (1, 0.7)]},  # combined probability >100%
        {"int": [(0, -0.4), (1, 0.7)]},  # probability for value 0 is invalid.
    ]

    for spv_dict in invalid_special_param_values_dicts:
        with pytest.raises(ValueError):
            LlamaTuneAdapter(
                orig_parameter_space=input_space,
                num_low_dims=2,
                special_param_values=spv_dict,
                max_unique_values_per_param=None,
            )


def gen_random_configs(adapter: LlamaTuneAdapter, num_configs: int) -> Iterator[CS.Configuration]:
    for sampled_config in adapter.target_parameter_space.sample_configuration(size=num_configs):
        # Transform low-dim config to high-dim config
        sampled_config_df = pd.DataFrame(
            [sampled_config.values()], columns=list(sampled_config.keys())
        )
        orig_config_df = adapter.transform(sampled_config_df)
        orig_config = CS.Configuration(
            adapter.orig_parameter_space,
            values=orig_config_df.iloc[0].to_dict(),
        )
        yield orig_config


def test_special_parameter_values_biasing() -> None:  # pylint: disable=too-complex
    """Tests LlamaTune's special parameter values biasing methodology."""
    input_space = CS.ConfigurationSpace(seed=1234)
    input_space.add_hyperparameter(
        CS.UniformIntegerHyperparameter(name="int_1", lower=0, upper=100)
    )
    input_space.add_hyperparameter(
        CS.UniformIntegerHyperparameter(name="int_2", lower=0, upper=100)
    )

    num_configs = 400
    bias_percentage = LlamaTuneAdapter.DEFAULT_SPECIAL_PARAM_VALUE_BIASING_PERCENTAGE
    eps = 0.2

    # Single parameter; single special value
    special_param_value_dicts: List[Dict[str, Any]] = [
        {"int_1": 0},
        {"int_1": (0, bias_percentage)},
        {"int_1": [0]},
        {"int_1": [(0, bias_percentage)]},
    ]

    for spv_dict in special_param_value_dicts:
        adapter = LlamaTuneAdapter(
            orig_parameter_space=input_space,
            num_low_dims=1,
            special_param_values=spv_dict,
            max_unique_values_per_param=None,
        )

        special_value_occurrences = sum(
            1 for config in gen_random_configs(adapter, num_configs) if config["int_1"] == 0
        )
        assert (1 - eps) * int(num_configs * bias_percentage) <= special_value_occurrences

    # Single parameter; multiple special values
    special_param_value_dicts = [
        {"int_1": [0, 1]},
        {"int_1": [(0, bias_percentage), (1, bias_percentage)]},
    ]

    for spv_dict in special_param_value_dicts:
        adapter = LlamaTuneAdapter(
            orig_parameter_space=input_space,
            num_low_dims=1,
            special_param_values=spv_dict,
            max_unique_values_per_param=None,
        )

        special_values_occurrences = {0: 0, 1: 0}
        for config in gen_random_configs(adapter, num_configs):
            if config["int_1"] == 0:
                special_values_occurrences[0] += 1
            elif config["int_1"] == 1:
                special_values_occurrences[1] += 1

        assert (1 - eps) * int(num_configs * bias_percentage) <= special_values_occurrences[0]
        assert (1 - eps) * int(num_configs * bias_percentage) <= special_values_occurrences[1]

    # Multiple parameters; multiple special values; different biasing percentage
    spv_dict = {
        "int_1": [(0, bias_percentage), (1, bias_percentage / 2)],
        "int_2": [(2, bias_percentage / 2), (100, bias_percentage * 1.5)],
    }
    adapter = LlamaTuneAdapter(
        orig_parameter_space=input_space,
        num_low_dims=1,
        special_param_values=spv_dict,
        max_unique_values_per_param=None,
    )

    special_values_instances: Dict[str, Dict[int, int]] = {
        "int_1": {0: 0, 1: 0},
        "int_2": {2: 0, 100: 0},
    }
    for config in gen_random_configs(adapter, num_configs):
        if config["int_1"] == 0:
            special_values_instances["int_1"][0] += 1
        elif config["int_1"] == 1:
            special_values_instances["int_1"][1] += 1

        if config["int_2"] == 2:
            special_values_instances["int_2"][2] += 1
        elif config["int_2"] == 100:
            special_values_instances["int_2"][100] += 1

    assert (1 - eps) * int(num_configs * bias_percentage) <= special_values_instances["int_1"][0]
    assert (1 - eps) * int(num_configs * bias_percentage / 2) <= special_values_instances["int_1"][
        1
    ]
    assert (1 - eps) * int(num_configs * bias_percentage / 2) <= special_values_instances["int_2"][
        2
    ]
    assert (1 - eps) * int(num_configs * bias_percentage * 1.5) <= special_values_instances[
        "int_2"
    ][100]


def test_max_unique_values_per_param() -> None:
    """Tests LlamaTune's parameter values discretization implementation."""
    # Define config space with a mix of different parameter types
    input_space = CS.ConfigurationSpace(seed=1234)
    input_space.add_hyperparameter(
        CS.UniformFloatHyperparameter(name="cont_1", lower=0, upper=5),
    )
    input_space.add_hyperparameter(
        CS.UniformFloatHyperparameter(name="cont_2", lower=1, upper=100)
    )
    input_space.add_hyperparameter(
        CS.UniformIntegerHyperparameter(name="int_1", lower=1, upper=10)
    )
    input_space.add_hyperparameter(
        CS.UniformIntegerHyperparameter(name="int_2", lower=0, upper=2048)
    )
    input_space.add_hyperparameter(
        CS.CategoricalHyperparameter(name="str_1", choices=["on", "off"])
    )
    input_space.add_hyperparameter(
        CS.CategoricalHyperparameter(name="str_2", choices=[f"choice_{idx}" for idx in range(10)])
    )

    # Restrict the number of unique parameter values
    num_configs = 200
    for max_unique_values_per_param in (5, 25, 100):
        adapter = LlamaTuneAdapter(
            orig_parameter_space=input_space,
            num_low_dims=3,
            special_param_values=None,
            max_unique_values_per_param=max_unique_values_per_param,
        )

        # Keep track of unique values generated for each parameter
        unique_values_dict: Dict[str, set] = {param: set() for param in list(input_space.keys())}
        for config in gen_random_configs(adapter, num_configs):
            for param, value in config.items():
                unique_values_dict[param].add(value)

        # Ensure that their number is less than the maximum number allowed
        for _, unique_values in unique_values_dict.items():
            assert len(unique_values) <= max_unique_values_per_param


@pytest.mark.parametrize(
    ("num_target_space_dims", "param_space_kwargs"),
    (
        [
            (num_target_space_dims, param_space_kwargs)
            for num_target_space_dims in (2, 4)
            for num_orig_space_factor in (1.5, 4)
            for param_space_kwargs in (
                {"n_continuous_params": int(num_target_space_dims * num_orig_space_factor)},
                {"n_integer_params": int(num_target_space_dims * num_orig_space_factor)},
                {"n_categorical_params": int(num_target_space_dims * num_orig_space_factor)},
                # Mix of all three types
                {
                    "n_continuous_params": int(num_target_space_dims * num_orig_space_factor / 3),
                    "n_integer_params": int(num_target_space_dims * num_orig_space_factor / 3),
                    "n_categorical_params": int(num_target_space_dims * num_orig_space_factor / 3),
                },
            )
        ]
    ),
)
def test_approx_inverse_mapping(
    num_target_space_dims: int,
    param_space_kwargs: dict,
) -> None:  # pylint: disable=too-many-locals
    """Tests LlamaTune's approximate high-to-low space projection method, using pseudo-
    inverse.
    """
    input_space = construct_parameter_space(**param_space_kwargs)

    # Enable low-dimensional space projection, but disable reverse mapping
    adapter = LlamaTuneAdapter(
        orig_parameter_space=input_space,
        num_low_dims=num_target_space_dims,
        special_param_values=None,
        max_unique_values_per_param=None,
        use_approximate_reverse_mapping=False,
    )

    sampled_config = input_space.sample_configuration()  # size=1)
    with pytest.raises(ValueError):
        sampled_config_df = pd.DataFrame(
            [sampled_config.values()], columns=list(sampled_config.keys())
        )
        _ = adapter.inverse_transform(sampled_config_df)

    # Enable low-dimensional space projection *and* reverse mapping
    adapter = LlamaTuneAdapter(
        orig_parameter_space=input_space,
        num_low_dims=num_target_space_dims,
        special_param_values=None,
        max_unique_values_per_param=None,
        use_approximate_reverse_mapping=True,
    )

    # Warning should be printed the first time
    sampled_config = input_space.sample_configuration()  # size=1)
    with pytest.warns(UserWarning):
        sampled_config_df = pd.DataFrame(
            [sampled_config.values()], columns=list(sampled_config.keys())
        )
        target_config_df = adapter.inverse_transform(sampled_config_df)
        # Low-dim (i.e., target) config should be valid
        target_config = CS.Configuration(
            adapter.target_parameter_space,
            values=target_config_df.iloc[0].to_dict(),
        )
        adapter.target_parameter_space.check_configuration(target_config)

    # Test inverse transform with 100 random configs
    for _ in range(100):
        sampled_config = input_space.sample_configuration()  # size=1)
        sampled_config_df = pd.DataFrame(
            [sampled_config.values()], columns=list(sampled_config.keys())
        )
        target_config_df = adapter.inverse_transform(sampled_config_df)
        # Low-dim (i.e., target) config should be valid
        target_config = CS.Configuration(
            adapter.target_parameter_space,
            values=target_config_df.iloc[0].to_dict(),
        )
        adapter.target_parameter_space.check_configuration(target_config)


@pytest.mark.parametrize(
    ("num_low_dims", "special_param_values", "max_unique_values_per_param"),
    (
        [
            (num_low_dims, special_param_values, max_unique_values_per_param)
            for num_low_dims in (8, 16)
            for special_param_values in (
                {"int_1": -1, "int_2": -1, "int_3": -1, "int_4": [-1, 0]},
                {
                    "int_1": (-1, 0.1),
                    "int_2": -1,
                    "int_3": (-1, 0.3),
                    "int_4": [(-1, 0.1), (0, 0.2)],
                },
            )
            for max_unique_values_per_param in (50, 250)
        ]
    ),
)
def test_llamatune_pipeline(
    num_low_dims: int,
    special_param_values: dict,
    max_unique_values_per_param: int,
) -> None:
    """Tests LlamaTune space adapter when all components are active."""
    # pylint: disable=too-many-locals

    # Define config space with a mix of different parameter types
    input_space = construct_parameter_space(
        n_continuous_params=10,
        n_integer_params=10,
        n_categorical_params=5,
    )
    adapter = LlamaTuneAdapter(
        orig_parameter_space=input_space,
        num_low_dims=num_low_dims,
        special_param_values=special_param_values,
        max_unique_values_per_param=max_unique_values_per_param,
    )

    special_value_occurrences = {
        # pylint: disable=protected-access
        param: {special_value: 0 for special_value, _ in tuples_list}
        for param, tuples_list in adapter._special_param_values_dict.items()
    }
    unique_values_dict: Dict[str, Set] = {param: set() for param in input_space.keys()}

    num_configs = 1000
    for config in adapter.target_parameter_space.sample_configuration(
        size=num_configs
    ):  # pylint: disable=not-an-iterable
        # Transform low-dim config to high-dim point/config
        sampled_config_df = pd.DataFrame([config.values()], columns=list(config.keys()))
        orig_config_df = adapter.transform(sampled_config_df)
        # High-dim (i.e., original) config should be valid
        orig_config = CS.Configuration(input_space, values=orig_config_df.iloc[0].to_dict())
        input_space.check_configuration(orig_config)

        # Transform high-dim config back to low-dim
        target_config_df = adapter.inverse_transform(orig_config_df)
        # Sampled config and this should be the same
        target_config = CS.Configuration(
            adapter.target_parameter_space,
            values=target_config_df.iloc[0].to_dict(),
        )
        assert target_config == config

        for param, value in orig_config.items():
            # Keep track of special value occurrences
            if param in special_value_occurrences:
                if value in special_value_occurrences[param]:
                    special_value_occurrences[param][value] += 1

            # Keep track of unique values generated for each parameter
            unique_values_dict[param].add(value)

    # Ensure that occurrences of special values do not significantly deviate from expected
    eps = 0.2
    for (
        param,
        tuples_list,
    ) in adapter._special_param_values_dict.items():  # pylint: disable=protected-access
        for value, bias_percentage in tuples_list:
            assert (1 - eps) * int(num_configs * bias_percentage) <= special_value_occurrences[
                param
            ][value]

    # Ensure that number of unique values is less than the maximum number allowed
    for _, unique_values in unique_values_dict.items():
        assert len(unique_values) <= max_unique_values_per_param


@pytest.mark.parametrize(
    ("num_target_space_dims", "param_space_kwargs"),
    (
        [
            (num_target_space_dims, param_space_kwargs)
            for num_target_space_dims in (2, 4)
            for num_orig_space_factor in (1.5, 4)
            for param_space_kwargs in (
                {"n_continuous_params": int(num_target_space_dims * num_orig_space_factor)},
                {"n_integer_params": int(num_target_space_dims * num_orig_space_factor)},
                {"n_categorical_params": int(num_target_space_dims * num_orig_space_factor)},
                # Mix of all three types
                {
                    "n_continuous_params": int(num_target_space_dims * num_orig_space_factor / 3),
                    "n_integer_params": int(num_target_space_dims * num_orig_space_factor / 3),
                    "n_categorical_params": int(num_target_space_dims * num_orig_space_factor / 3),
                },
            )
        ]
    ),
)
def test_deterministic_behavior_for_same_seed(
    num_target_space_dims: int,
    param_space_kwargs: dict,
) -> None:
    """Tests LlamaTune's space adapter deterministic behavior when given same seed in
    the input parameter space.
    """

    def generate_target_param_space_configs(seed: int) -> List[CS.Configuration]:
        input_space = construct_parameter_space(**param_space_kwargs, seed=seed)

        # Init adapter and sample points in the low-dim space
        adapter = LlamaTuneAdapter(
            orig_parameter_space=input_space,
            num_low_dims=num_target_space_dims,
            special_param_values=None,
            max_unique_values_per_param=None,
            use_approximate_reverse_mapping=False,
        )

        sample_configs: List[CS.Configuration] = (
            adapter.target_parameter_space.sample_configuration(size=100)
        )
        return sample_configs

    assert generate_target_param_space_configs(42) == generate_target_param_space_configs(42)
    assert generate_target_param_space_configs(1234) != generate_target_param_space_configs(42)

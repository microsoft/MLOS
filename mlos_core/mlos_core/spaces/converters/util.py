#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Helper functions for config space converters."""

from ConfigSpace import ConfigurationSpace
from ConfigSpace.functional import quantize
from ConfigSpace.hyperparameters import Hyperparameter, NumericalHyperparameter

QUANTIZATION_BINS_META_KEY = "quantization_bins"


def monkey_patch_hp_quantization(hp: Hyperparameter) -> None:
    """
    Monkey-patch quantization into the Hyperparameter.

    Temporary workaround to dropped quantization support in ConfigSpace 1.0
    See Also: <https://github.com/automl/ConfigSpace/issues/390>

    Parameters
    ----------
    hp : NumericalHyperparameter
        ConfigSpace hyperparameter to patch.
    """

    if not isinstance(hp, NumericalHyperparameter):
        return

    assert isinstance(hp, NumericalHyperparameter)
    quantization_bins = (hp.meta or {}).get(QUANTIZATION_BINS_META_KEY)
    if quantization_bins is None:
        # No quantization requested.
        # Remove any previously applied patches.
        if hasattr(hp, "sample_value_mlos_orig"):
            setattr(hp, "sample_value", hp.sample_value_mlos_orig)
            delattr(hp, "sample_value_mlos_orig")
        return

    try:
        quantization_bins = int(quantization_bins)
    except ValueError as ex:
        raise ValueError(f"{quantization_bins=} :: must be an integer.") from ex

    if quantization_bins <= 1:
        raise ValueError(f"{quantization_bins=} :: must be greater than 1.")

    if not hasattr(hp, "sample_value_mlos_orig"):
        setattr(hp, "sample_value_mlos_orig", hp.sample_value)

    assert hasattr(hp, "sample_value_mlos_orig")
    setattr(
        hp,
        "sample_value",
        lambda size=None, **kwargs: quantize(
            hp.sample_value_mlos_orig(size, **kwargs),
            bounds=(hp.lower, hp.upper),
            bins=quantization_bins,
        ).astype(type(hp.default_value)),
    )


def monkey_patch_cs_quantization(cs: ConfigurationSpace) -> None:
    """
    Monkey-patch quantization into the Hyperparameters of a ConfigSpace.

    Parameters
    ----------
    cs : ConfigurationSpace
        ConfigSpace to patch.
    """
    for hp in cs.values():
        monkey_patch_hp_quantization(hp)

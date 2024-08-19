#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Helper functions for config space converters."""

from ConfigSpace.functional import quantize
from ConfigSpace.hyperparameters import NumericalHyperparameter


def monkey_patch_quantization(hp: NumericalHyperparameter, quantization_bins: int) -> None:
    """
    Monkey-patch quantization into the Hyperparameter.

    Parameters
    ----------
    hp : NumericalHyperparameter
        ConfigSpace hyperparameter to patch.
    quantization_bins : int
        Number of bins to quantize the hyperparameter into.
    """
    if quantization_bins <= 1:
        raise ValueError(f"{quantization_bins=} :: must be greater than 1.")

    # Temporary workaround to dropped quantization support in ConfigSpace 1.0
    # See Also: https://github.com/automl/ConfigSpace/issues/390
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

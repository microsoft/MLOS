#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Helper functions for config space converters."""

from ConfigSpace import ConfigurationSpace
from ConfigSpace.functional import quantize
from ConfigSpace.hyperparameters import Hyperparameter, NumericalHyperparameter

QUANTIZATION_BINS_META_KEY = "quantization_bins"


def monkey_patch_hp_quantization(hp: Hyperparameter) -> Hyperparameter:
    """
    Monkey-patch quantization into the Hyperparameter.

    Temporary workaround to dropped quantization support in ConfigSpace 1.0
    See Also: <https://github.com/automl/ConfigSpace/issues/390>

    Parameters
    ----------
    hp : Hyperparameter
        ConfigSpace hyperparameter to patch.

    Returns
    -------
    hp : Hyperparameter
        Patched hyperparameter.
    """
    if not isinstance(hp, NumericalHyperparameter):
        return hp

    assert isinstance(hp, NumericalHyperparameter)
    dist = hp._vector_dist  # pylint: disable=protected-access
    quantization_bins = (hp.meta or {}).get(QUANTIZATION_BINS_META_KEY)
    if quantization_bins is None:
        # No quantization requested.
        # Remove any previously applied patches.
        if hasattr(dist, "sample_vector_mlos_orig"):
            setattr(dist, "sample_vector", dist.sample_vector_mlos_orig)
            delattr(dist, "sample_vector_mlos_orig")
        return hp

    try:
        quantization_bins = int(quantization_bins)
    except ValueError as ex:
        raise ValueError(f"{quantization_bins=} :: must be an integer.") from ex

    if quantization_bins <= 1:
        raise ValueError(f"{quantization_bins=} :: must be greater than 1.")

    if not hasattr(dist, "sample_vector_mlos_orig"):
        setattr(dist, "sample_vector_mlos_orig", dist.sample_vector)

    assert hasattr(dist, "sample_vector_mlos_orig")
    setattr(
        dist,
        "sample_vector",
        lambda n, *, seed=None: quantize(
            dist.sample_vector_mlos_orig(n, seed=seed),
            bounds=(dist.lower_vectorized, dist.upper_vectorized),
            bins=quantization_bins,
        ),
    )
    return hp


def monkey_patch_cs_quantization(cs: ConfigurationSpace) -> ConfigurationSpace:
    """
    Monkey-patch quantization into the Hyperparameters of a ConfigSpace.

    Parameters
    ----------
    cs : ConfigurationSpace
        ConfigSpace to patch.

    Returns
    -------
    cs : ConfigurationSpace
        Patched ConfigSpace.
    """
    for hp in cs.values():
        monkey_patch_hp_quantization(hp)
    return cs

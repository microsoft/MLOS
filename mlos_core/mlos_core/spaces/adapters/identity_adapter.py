#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Contains the Identity (no-op) Space Adapter class."""

import ConfigSpace
import pandas as pd

from mlos_core.spaces.adapters.adapter import BaseSpaceAdapter


class IdentityAdapter(BaseSpaceAdapter):
    """
    Identity (no-op) SpaceAdapter class.

    Parameters
    ----------
    orig_parameter_space : ConfigSpace.ConfigurationSpace
        The original parameter space to explore.
    """

    @property
    def target_parameter_space(self) -> ConfigSpace.ConfigurationSpace:
        return self._orig_parameter_space

    def transform(self, configuration: pd.DataFrame) -> pd.DataFrame:
        return configuration

    def inverse_transform(self, configurations: pd.DataFrame) -> pd.DataFrame:
        return configurations

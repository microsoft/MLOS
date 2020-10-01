#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from abc import ABC, abstractmethod


class UtilityFunction(ABC):
    """ Base class for all Utility Functions.

    """

    @abstractmethod
    def __call__(self, feature_values_pandas_frame):
        raise NotImplementedError("All subclasses must implement this.")

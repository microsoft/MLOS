#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from abc import ABC, abstractmethod
from mlos.Optimizers.ParetoFrontier import ParetoFrontier


class UtilityFunction(ABC):
    """ Base class for all Utility Functions.

    """

    @abstractmethod
    def __call__(self, feature_values_pandas_frame, pareto_frontier: ParetoFrontier = None):
        raise NotImplementedError("All subclasses must implement this.")

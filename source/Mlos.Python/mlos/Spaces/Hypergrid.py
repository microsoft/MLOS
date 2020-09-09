#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from abc import ABC, abstractmethod
import random
import pandas as pd
from mlos.Spaces.Dimensions.Dimension import Dimension


class Hypergrid(ABC):
    """ A base class for all search-space-like classes.

    """

    def __init__(self, name=None, random_state=None):
        self.name = name
        if random_state is None:
            random_state = random.Random()
        self._random_state = random_state

    @abstractmethod
    def __contains__(self, item):
        raise NotImplementedError("All subclasses must implement this.")

    @abstractmethod
    def __getitem__(self, item):
        raise NotImplementedError

    @property
    @abstractmethod
    def random_state(self):
        return self._random_state

    @random_state.setter
    @abstractmethod
    def random_state(self, value):
        raise NotImplementedError("This has to be implemented in all derived classes to set random_state on individual dimensions.")

    @property
    @abstractmethod
    def dimensions(self):
        raise NotImplementedError("All subclasses must implement this.")

    @abstractmethod
    def get_dimensions_for_point(self, point, return_join_dimensions=True):
        raise NotImplementedError("All subclasses must implement this.")

    @abstractmethod
    def random(self, point=None):
        raise NotImplementedError("All subclasses must implement this.")

    def random_dataframe(self, num_samples):
        config_dicts = [
            {dim_name: value for dim_name, value in self.random()}
            for _ in range(num_samples)
        ]
        return pd.DataFrame(config_dicts)

    @abstractmethod
    def join(self, subgrid, on_external_dimension: Dimension):
        raise NotImplementedError("All subclasses must implement this.")

    @abstractmethod
    def is_hierarchical(self):
        raise NotImplementedError("All subclasses must implement this.")

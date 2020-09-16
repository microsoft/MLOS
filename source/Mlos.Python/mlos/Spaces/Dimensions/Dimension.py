#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from abc import ABC, abstractmethod
import random

class Dimension(ABC):
    """ An abstract class representing a set of values a given parameter can take.

    This is a base class for: EmptyDimension, ContinuousDimension, DiscreteDimension, OrdinalDimension,
    CategoricalDimension, and CompositeDimension.

    We want to ascertain that all of those subclasses implement the Dimension interface.

    Dimensions are generally used to represent legal values for a parameter. When we take a cross-product of several
    dimensions we end up with a hypergrid.

    Notably, Dimensions have set semantics - we should be able to efficiently perform union, intersection, and
    difference operations, as well as determine membership of a value in this set or generate random values along
    a dimension from any given distribution.

    """

    @classmethod
    def flatten_dimension_name(cls, dimension_name: str):
        return dimension_name.replace(".", "___")

    @classmethod
    def split_dimension_name(cls, dimension_name):
        dimension_name_chunks = dimension_name.split(".")
        if len(dimension_name_chunks) == 1:
            subgrid_name = None
            dimension_name_without_subgrid_name = dimension_name
        else:
            subgrid_name = dimension_name_chunks[0]
            dimension_name_without_subgrid_name = ".".join(dimension_name_chunks[1:])
        return subgrid_name, dimension_name_without_subgrid_name

    #  If a discrete, categorical or ordinal dimension is INNUMERABLY_LARGE then we refrain from enumerating it's members.
    INNUMERABLY_LARGE = 1000 * 1000

    def __init__(self, name, random_state=None):
        #assert "." not in name, 'Dimension names cannot contain "." characters.'
        #assert "::" not in name, 'Dimension names cannot contain "::" character sequences'
        self.name = name
        if random_state is None:
            random_state = random.Random()
        self._random_state = random_state

    def flatten_name(self):
        self.name = self.flatten_dimension_name(dimension_name=self.name)
        return self

    @property
    def random_state(self):
        return self._random_state

    @random_state.setter
    def random_state(self, value):
        self._random_state = value

    @abstractmethod
    def copy(self):
        raise NotImplementedError

    def __str__(self):
        return self.to_string(include_name=True)

    def __repr__(self):
        return self.to_string(include_name=True)

    @abstractmethod
    def to_string(self, include_name=True):
        raise NotImplementedError

    @abstractmethod
    def __contains__(self, item):
        raise NotImplementedError

    @abstractmethod
    def __len__(self):
        raise NotImplementedError

    @abstractmethod
    def __iter__(self):
        raise NotImplementedError

    @abstractmethod
    def __eq__(self, other):
        raise NotImplementedError

    def __ne__(self, other):
        return not self == other

    def __and__(self, other):
        return self.intersection(other)

    def __or__(self, other):
        return self.union(other)

    def __sub__(self, other):
        return self.difference(other)

    @property
    def is_innumerably_large(self):
        # innumerably large dimensions are so large that an attempt to iterate over them is impractical
        return len(self) > self.INNUMERABLY_LARGE

    @abstractmethod
    def intersects(self, other):
        raise NotImplementedError

    @abstractmethod
    def intersection(self, other):
        raise NotImplementedError

    @abstractmethod
    def union(self, other):
        raise NotImplementedError

    @abstractmethod
    def difference(self, other):
        raise NotImplementedError

    @abstractmethod
    def linspace(self, num=100):
        """ Similar to numpy's linspace. Returns an iterable of num elements linearly distributed along the dimension.

        :param num:
        :return:
        """
        raise NotImplementedError

    @abstractmethod
    def random(self):
        raise NotImplementedError

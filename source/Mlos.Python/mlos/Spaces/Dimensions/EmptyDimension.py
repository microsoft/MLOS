#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from .Dimension import Dimension


class EmptyDimension(Dimension):

    # pylint: disable=redefined-builtin
    def __init__(self, name, type):
        super(EmptyDimension, self).__init__(name=name)
        self.type = type

    def __str__(self):
        return self.to_string(include_name=False)

    def to_string(self, include_name=True):
        if include_name:
            return self.name + ": {}"
        return "{}"

    def __repr__(self):
        return self.to_string(include_name=True)

    @property
    def is_innumerably_large(self):
        return False

    def copy(self):
        return EmptyDimension(name=self.name, type=self.type)

    def __contains__(self, item):
        return isinstance(item, EmptyDimension)

    def __len__(self):
        return 0

    def __iter__(self):
        for item in []:
            yield item

    def __eq__(self, other):
        return isinstance(other, EmptyDimension) and (self.name == other.name) and (self.type == other.type)

    def difference(self, other):
        raise NotImplementedError("Did you remember to import DimensionCalulator?")

    def intersection(self, other):
        raise NotImplementedError("Did you remember to import DimensionCalulator?")

    def intersects(self, other):
        raise NotImplementedError("Did you remember to import DimensionCalulator?")

    def union(self, other):
        raise NotImplementedError("Did you remember to import DimensionCalulator?")

    def contains_dimension(self, other):
        raise NotImplementedError("Did you remember to import DimensionCalulator?")

    def equals(self, other):
        raise NotImplementedError("Did you remember to import DimensionCalulator?")

    def random(self): # pylint: disable=no-self-use
        return None

    def linspace(self, num=100): # pylint: disable=unused-argument,no-self-use
        return []

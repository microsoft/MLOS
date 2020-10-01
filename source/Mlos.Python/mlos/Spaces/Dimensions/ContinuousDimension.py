#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import math
from numbers import Number
import numpy as np

from .Dimension import Dimension
from .EmptyDimension import EmptyDimension


class ContinuousDimension(Dimension):
    """ Models a dimension that can assume continuous values.

    """

    def __init__(self, name, min=None, max=None, include_min=True, include_max=True, random_state=None): # pylint: disable=redefined-builtin
        super(ContinuousDimension, self).__init__(name=name, random_state=random_state)
        if min > max:
            min, max = max, min
        self.min = min
        self.max = max
        if min == max:
            # we have an empty set if either include_min or include_max are False
            # and a set containing one point if both are true
            include_min = include_min and include_max
            include_max = include_min

        self.include_min = include_min
        self.include_max = include_max

    @property
    def width(self):
        return self.max - self.min

    def make_empty(self):
        return EmptyDimension(name=self.name, type=ContinuousDimension)

    def copy(self):
        return ContinuousDimension(
            name=self.name,
            min=self.min,
            max=self.max,
            include_min=self.include_min,
            include_max=self.include_max
        )

    def __eq__(self, other):
        if not isinstance(other, ContinuousDimension):
            raise ValueError(f"Cannot determine equality between an instance of {type(self)} and and instance of {type(other)}.")
        return self.name == other.name \
               and self.min == other.min \
               and self.max == other.max \
               and self.include_min == other.include_min \
               and self.include_max == other.include_max


    def __repr__(self):
        """ Returns a string representation of this continuous dimension.

        In some circles the usage of '[' and ']' convey that the boundary points of a set are included,
        whereas '(' and ')' denote a set where the boundary point is not included.

        Examples:
            (2, 5] - a set of all real numbers between 2 and 5, where 2 is not a member of the set, but 5 is.
            [-1, 1] - both -1 and 1 are members of that set
            (-1, 1) - neither -1 nor 1 are members of the set.
        :return:
        """
        return self.to_string(include_name=True)

    def to_string(self, include_name=True):
        return f"{self.name + ': ' if include_name else ''}{'[' if self.include_min else '('}{self.min:.2f}, {self.max:.2f}{']' if self.include_max else ')'}"

    def __len__(self):
        if (self.max == self.min) and self.include_max and self.include_min:
            return 1
        return math.inf

    def __iter__(self):
        if self.is_innumerably_large:
            raise RuntimeError("This set is too large to enumerate.")
        yield self.min

    def __contains__(self, item):
        if isinstance(item, Number):
            return self._contains_number(number=item)

        if isinstance(item, Dimension):
            other_dimension = item
            return self.contains_dimension(other_dimension)

        raise NotImplementedError(f"Don't know how to test containment of {type(item)} objects.")

    def __and__(self, other):
        return self.intersection(other)

    def __or__(self, other):
        return self.union(other)

    def intersects_continuous_dimension(self, other):
        assert isinstance(other, ContinuousDimension)
        assert self.name == other.name

        if self.min > other.max or other.min > self.max:
            return False  # they don't intersect

        if self.min == other.max and (not self.include_min or not other.include_max):
            return False  # they are contiguous but don't overlap

        if other.min == self.max and (not other.include_min or not self.include_max):
            return False  # they are contiguous but don't overlap

        return True

    def intersection_continuous_dimension(self, other):
        assert isinstance(other, ContinuousDimension)

        if not self.intersects_continuous_dimension(other):
            return self.make_empty()

        # If they do intersect, we take the larger min and the smaller max paying attention to 'include_min' and 'include_max'
        # There are a few cases here so let's first figure out the values of the attributes and then create the intersection.
        intersection_include_min = None
        intersection_include_max = None
        if self.min < other.min:
            intersection_include_min = other.include_min
        elif self.min > other.min:
            intersection_include_min = self.include_min
        else:
            intersection_include_min = self.include_min and other.include_min

        if self.max > other.max:
            # we take the smaller max and it's inclusion
            intersection_include_max = other.include_max
        elif self.max < other.max:
            intersection_include_max = self.include_max
        else:
            intersection_include_max = self.include_max and other.include_max

        intersection = ContinuousDimension(
            name=self.name,
            min=max(self.min, other.min),
            max=min(self.max, other.max),
            include_min=intersection_include_min,
            include_max=intersection_include_max
        )
        return intersection

    def union_overlapping_continuous_dimension(self, other):
        assert isinstance(other, ContinuousDimension)
        assert self.intersects(other)
        union = ContinuousDimension(
            name=self.name,
            min=min(self.min, other.min),
            max=max(self.max, other.max)
        )

        if self.min < other.min:
            union.include_min = self.include_min  # pylint: disable=attribute-defined-outside-init
        elif self.min > other.min:
            union.include_min = other.include_min  # pylint: disable=attribute-defined-outside-init
        else:
            union.include_min = self.include_min or other.include_min  # pylint: disable=attribute-defined-outside-init

        if self.max > other.max:
            union.include_max = self.include_max  # pylint: disable=attribute-defined-outside-init
        elif self.max < other.max:
            union.include_max = other.include_max  # pylint: disable=attribute-defined-outside-init
        else:
            union.include_max = self.include_max or other.include_max  # pylint: disable=attribute-defined-outside-init

        return union

    def split_on(self, other):
        """ Splits self on the other continuous dimension.

        """
        left = None
        right = None

        intersection = self.intersection(other)
        if isinstance(intersection, EmptyDimension):
            left = self.copy()
            right = self.make_empty()
            return left, right

        if intersection.min == self.min:
            if self.include_min and not intersection.include_min:
                left = ContinuousDimension(name=self.name, min=self.min, max=self.min)
            else:
                left = self.make_empty()
        else:
            left = ContinuousDimension(
                name=self.name,
                min=self.min,
                max=intersection.min,
                include_min=self.include_min,
                include_max=not intersection.include_min
            )

        if intersection.max == self.max:
            if self.include_max and not intersection.include_max:
                right = ContinuousDimension(name=self.name, min=self.max, max=self.max)
            else:
                right = self.make_empty()
        else:
            right = ContinuousDimension(
                name=self.name,
                min=intersection.max,
                max=self.max,
                include_min=not intersection.include_max,
                include_max=self.include_max
            )

        return left, right

    def linspace(self, num=1000):
        # TODO: fix the includes
        return np.linspace(self.min, self.max, num)

    def random(self):
        if self.width == 0 and not (self.include_min or self.include_min):
            raise ValueError("Cannot generate a random value from an empty dimension.")
        if self.width == math.inf:
            raise ValueError("Cannot generate a random value from an unbounded dimension.")
        ret_val = None
        while ret_val is None or (ret_val == self.min and not self.include_min):
            ret_val = self._random_state.random() * self.width + self.min
        return ret_val


    def _contains_number(self, number):
        assert isinstance(number, Number)
        if number < self.min or number > self.max:
            return False
        if not self.include_min and number == self.min:
            return False
        if not self.include_max and number == self.max:
            return False
        return self.min <= number <= self.max

    def contains_continuous_dimension(self, other):
        assert isinstance(other, ContinuousDimension)
        if other.name != self.name:
            return False

        if other.include_min and other.min not in self:
            return False
        if other.include_max and other.max not in self:
            return False

        return other.min >= self.min and other.max <= self.max

    def is_contiguous_with(self, other):
        assert isinstance(other, ContinuousDimension)
        return (self.min == other.max and (self.include_min != other.include_max)) \
            or \
               (self.max == other.min and (self.include_max != other.include_min))

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

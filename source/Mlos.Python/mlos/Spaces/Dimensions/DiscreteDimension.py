#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import math
from numbers import Number
import numpy as np

from .Dimension import Dimension
from .EmptyDimension import EmptyDimension


class DiscreteDimension(Dimension):
    """ Models a dimension whose values can assume uniformly spaced discrete values.

    #TODO: rename to IntegerDimension.

    """

    def __init__(self, name, min, max, random_state=None): # pylint: disable=redefined-builtin
        super(DiscreteDimension, self).__init__(name=name, random_state=random_state)
        # self.stride used to be any integer, but that makes unions very cumbersome.
        # TODO: make stride variable again
        self.stride = 1

        if min > max:
            min, max = max, min

        self.min = min
        self.max = max

    def make_empty(self):
        return EmptyDimension(name=self.name, type=DiscreteDimension)

    def is_contiguous_with(self, other):
        assert isinstance(other, DiscreteDimension)
        if not self.stride == other.stride:
            return False

        return self.min == (other.max + other.stride) or other.min == (self.max + self.stride)

    def copy(self):
        return DiscreteDimension(
            name=self.name,
            min=self.min,
            max=self.max
        )

    def __eq__(self, other):
        return isinstance(other, DiscreteDimension) \
               and other.name == self.name \
               and other.min == self.min \
               and other.max == self.max \
               and other.stride == self.stride

    def __repr__(self):
        return self.to_string(include_name=True)

    def to_string(self, include_name=True):
        if len(self) == 1:
            return f"{self.name + ': ' if include_name else ''}{{{self.min}}}"
        if len(self) == 2:
            return f"{self.name + ': ' if include_name else ''}{{{self.min}, {self.max}}}"
        if len(self) == 3:
            return f"{self.name + ': ' if include_name else ''}{{{self.min}, {self.min + self.stride}, {self.max}}}"
        return f"{self.name + ': ' if include_name else ''}{{{self.min}, {self.min + self.stride}, ... , {self.max}}}"

    def __len__(self):
        return self.max - self.min + 1

    def __iter__(self):
        if self.is_innumerably_large:
            raise RuntimeError("This set is too large to enumerate.")
        current = self.min
        while current <= self.max:
            yield current
            current += self.stride

    def __contains__(self, item):
        if isinstance(item, Number):
            if not self.min <= item <= self.max:
                # if it's out of bounds it's not in :)
                return False
            # it's in bounds but is it on the stride?
            strides_away_from_min = (item - self.min) / self.stride
            return int(strides_away_from_min) == strides_away_from_min
        if isinstance(item, Dimension):
            # So it's a dimension... for each type of dimension we need a separate logic
            other_dimension = item
            assert self.name == other_dimension.name

            if isinstance(other_dimension, DiscreteDimension):
                # we need to make sure that it's in bounds, on stride, and strides harmonize
                if not(other_dimension.min in self and other_dimension.max in self):
                    # it's not in bounds
                    return False
                # OK: it's within bounds and on stride, but do strides harmonize?
                # the strides harmonize if the other_dimension.stride is a multiple of our stride
                stride_ratio = other_dimension.stride / self.stride
                return int(stride_ratio) == stride_ratio
            return False
        return False

    def intersection_discrete_dimension(self, other):
        assert isinstance(other, DiscreteDimension)
        assert self.name == other.name

        assert isinstance(other, DiscreteDimension)
        if self.min > other.max or other.min > self.max:
            # they don't intersect
            return self.make_empty()

        # now the tricky part...
        # we need to find the first point of intersection.. so solve for A and B, where they are integers:
        # self.min + A * self.stride = other.min + B * other.stride
        # AND self.min + A * self.stride <= self.max
        # AND other.min + B * other.stride <= other.max => (self.stride / other.stride) * A + (self.min - other.min) = B
        # SUBJECT TO: A <= (self.max - self.min) / self.stride AND B <= other.max - other.min) / other.stride
        # we also know that we have to examine at most  (LeastCommonMultiple(self.stride, other.stride) / max(self.stride, other.stride)

        least_common_multiple = self.least_common_multiple(self.stride, other.stride)

        potential_intersection_min, iterating_self = max(self.min, other.min), other.min <= self.min <= other.max
        iterating_stride = self.stride if iterating_self else other.stride
        num_attempts_remaining = least_common_multiple / iterating_stride
        intersection_min = None
        while num_attempts_remaining > 0:
            if potential_intersection_min in self and potential_intersection_min in other:
                intersection_min = potential_intersection_min
                break
            potential_intersection_min += iterating_stride
            num_attempts_remaining -= 1

        if intersection_min is None:
            # We didn't find any point of intersection
            return self.make_empty()

        # We found the intersection min, now we need to find the max
        upper_ceiling_on_max = min(self.max, other.max)
        intersection_stride = least_common_multiple
        intersection_max = intersection_min + math.floor((upper_ceiling_on_max - intersection_min) / intersection_stride) * intersection_stride
        return DiscreteDimension(name=self.name, min=intersection_min, max=intersection_max)


    def union_contiguous_discrete_dimension(self, other):
        assert isinstance(other, DiscreteDimension)
        assert self.intersects(other) or self.is_contiguous_with(other)

        return DiscreteDimension(
            name=self.name,
            min=min(self.min, other.min),
            max=max(self.max, other.max)
        )


        ##  THE CODE BELOW IS AN OLD IMPLEMENTATION. IT HAS THE LOGIC TO DEAL WITH DIFFERENT
        ## STRIDES. I'M KEEPING IT HERE FOR FUTURE REFERENCE ONLY.
        ##

        # here we go again... overlapping discrete dimensions can:
        #   * either not interleave (i.e. self.min > other.max or self.max < other.min) => Easy: return both
        #   * share an end-point: self.min == other.max or self.max == other.min => just remove the shared endpoint from one and return both
        #   * overlap and have the same stride (or one stride is a multiple of another) and they actually have an intersection
        #       => make the overlapping interval part of the denser dimension
        #   * overlap and yet have disharmonized strides => degrade to OrdinalDimension

        #if self.min > other.max:
        #    return CompositeDimension(name=self.name, chunks_type=DiscreteDimension, chunks=[other, self])
        #if other.min > self.max:
        #    return CompositeDimension(name=self.name, chunks_type=DiscreteDimension, chunks=[self, other])

        #if self.min == other.max:
        #    _, upper_part = self.split_on(other.max)
        #    return CompositeDimension(name=self.name, chunks_type=DiscreteDimension, chunks=[other, upper_part])
        #if other.min == self.max:
        #    _, upper_part = other.split_on(self.max)
        #    return CompositeDimension(name=self.name, chunks_type=DiscreteDimension, chunks=[self, upper_part])

        #strides_gcd = self.greatest_common_divisor(self.stride, other.stride)

        #if isinstance(self.intersection(other), EmptyDimension) or strides_gcd not in (self.stride, other.stride):
        #    # they may overlap but they don't share anything...
        #    # TODO: let's produce the smallest possible OrdinalSet
        #    # meanwhile let's just produce an ordinal set
        #    raise NotImplementedError("This returns an OrdinalDimension which doesn't yet play with the rest of the type system.")
        #    values_set = {value for value in self}
        #    for value in other:
        #        values_set.add(value)
        #    ordered_values = sorted(list(values_set))
        #    return OrdinalDimension(name=self.name, ordered_values=ordered_values)

        #if strides_gcd in (self.stride, other.stride):
        #    denser = self
        #    sparser = other
        #    if strides_gcd == other.stride:
        #        denser = other
        #        sparser = self

        #    # we include all of denser and whatever remains in sparser
        #    sparser_lower_part, _ = sparser.split_on(denser.min)
        #    _, sparser_upper_part = sparser.split_on(denser.max)
        #    chunks = []
        #    if sparser_lower_part is not None:
        #        chunks.append(sparser_lower_part)
        #    chunks.append(denser)
        #    if sparser_upper_part is not None:
        #        chunks.append(sparser_upper_part)
        #    return CompositeDimension(name=self.name, chunks_type=DiscreteDimension, chunks=chunks)

    def split_on(self, split_value, include_in_left=False, include_in_right=False):
        # splits the discrete dimension into two and excludes the split value from both
        left = self.make_empty()
        right = self.make_empty()

        if split_value < self.min:
            right = self.copy()

        elif split_value > self.max:
            left = self.copy()

        elif self.min < split_value < self.max:
            if include_in_left:
                left = DiscreteDimension(name=self.name, min=self.min, max=split_value)
            else:
                left = DiscreteDimension(name=self.name, min=self.min, max=split_value - 1)

            if include_in_right:
                right = DiscreteDimension(name=self.name, min=split_value, max=self.max)
            else:
                right = DiscreteDimension(name=self.name, min=split_value + 1, max=self.max)

        elif split_value == self.min and split_value == self.max:
            if include_in_left:
                left = DiscreteDimension(name=self.name, min=self.min, max=split_value)

            if include_in_right:
                right = DiscreteDimension(name=self.name, min=split_value, max=self.max)

        elif split_value == self.min:
            if include_in_left:
                left = DiscreteDimension(name=self.name, min=self.min, max=split_value)

            if include_in_right:
                right = DiscreteDimension(name=self.name, min=split_value, max=self.max)
            else:
                right = DiscreteDimension(name=self.name, min=split_value + self.stride, max=self.max)

        elif split_value == self.max:
            if include_in_left:
                left = DiscreteDimension(name=self.name, min=self.min, max=split_value)
            else:
                left = DiscreteDimension(name=self.name, min=self.min, max=split_value - self.stride)

            if include_in_right:
                right = DiscreteDimension(name=self.name, min=split_value + self.stride, max=self.max)

        return left, right

        # CODE BELOW DEALS WITH DIFFERENT STRIDE LENGTHS AND WE KEEP IT FOR FUTURE REFERENCE.
        # let's find the lower part
        #lower_part_min = self.min
        #lower_part_max = self.min + math.floor((split_value - self.min)/self.stride) * self.stride
        #if lower_part_max == split_value:
        #    lower_part_max -= self.stride
        #lower_part = DiscreteDimension(name=self.name, min=lower_part_min, max=lower_part_max)

        ## now the upper part
        #upper_part_max = self.max
        #upper_part_min = lower_part_max + self.stride
        #if upper_part_min == split_value:
        #    upper_part_min += self.stride
        #upper_part = DiscreteDimension(name=self.name, min=upper_part_min, max=upper_part_max)

        #return lower_part, upper_part

    @staticmethod
    def greatest_common_divisor(a, b):
        while b > 0:
            a, b = b, a % b
        return a

    @staticmethod
    def least_common_multiple(a, b):
        return int((a * b) / DiscreteDimension.greatest_common_divisor(a, b))

    def linspace(self, num=None):

        if num is None:
            num = min(len(self), 1000)

        # The easiest way to do it is to generate a linspace from numpy, and round all numbers to integers.
        #
        return np.rint(np.linspace(self.min, self.max, num)).astype(int).tolist()

    def random(self):
        assert self.stride == 1
        return self._random_state.randint(self.min, self.max)

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

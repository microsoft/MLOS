#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import math
from numbers import Number
import numpy as np

from .Dimension import Dimension
from .IntervalTree import IntervalTree


class CompositeDimension(Dimension):
    """ Models a union of discontinuous ContinuousDimensions or DiscreteDimensions.

    A union or difference operation on two ContinuousDimensions (or two DiscreteDimensions) can lead to
    a result comprised by discontinuous sets. In order to support further efficient operations on the
    result, we maintain such a union in an interval tree data structure.
    """

    def __init__(self, name, chunks_type, chunks=None):
        super(CompositeDimension, self).__init__(name=name)
        self.chunks_type = chunks_type
        self._interval_tree = IntervalTree(name=self.name, chunks_type=self.chunks_type)
        if chunks is not None:
            for chunk in chunks:
                self._interval_tree.add(chunk)

    def __str__(self):
        return self.to_string(include_name=True)

    def to_string(self, include_name=True):
        chunks_string = " UNION ".join(chunk.to_string(include_name=False) for chunk in self.enumerate_chunks())
        if include_name:
            return f"{self.name}: {chunks_string}"
        return chunks_string

    def __repr__(self):
        return self.to_string(include_name=True)

    def copy(self):
        copy = CompositeDimension(
            name=self.name,
            chunks_type=self.chunks_type
        )
        copy._interval_tree = self._interval_tree.copy()  # pylint: disable=protected-access
        return copy

    def __contains__(self, item):
        if isinstance(item, Number):
            return self.contains_number(item)
        if isinstance(item, Dimension):
            return self.contains_dimension(item)
        raise NotImplementedError

    def __len__(self):
        length = 0
        for chunk in self.enumerate_chunks():
            length += len(chunk)
            if math.isinf(length):
                break
        return length

    def __iter__(self):
        if self.is_innumerably_large:
            raise RuntimeError("This set is too large to enumerate.")
        for chunk in self.enumerate_chunks():
            for element in chunk:
                yield element

    def __eq__(self, other):
        return self.equals(other)

    def linspace(self, num=100):
        """ Generates an iterable of numbers linearly distributed between min and max of the dimension.

        To do that we need to:
        1. Find the range of this dimension (diff between smallest and largest member)
        2. Find how much of the range is occupied.
        3. For each chunk, enumerate a number of elements proportional to it's size in the range.

        :param num:
        :return:
        """
        # TODO: fix the rounding problems
        total_length = sum((chunk.max - chunk.min) for chunk in self.enumerate_chunks())
        partial_linspaces = []
        for chunk in self.enumerate_chunks():
            chunk_length = chunk.max - chunk.min
            chunk_size_proportion = (chunk_length * 1.0 / total_length)
            num_elements = round(chunk_size_proportion * num)
            partial_linspaces.append(chunk.linspace(num=num_elements))
        return np.concatenate(partial_linspaces)

    def contains_number(self, number):
        # TODO: improve perf
        return any(number in node.payload for node in self._interval_tree.enumerate())

    def enumerate_chunks(self):
        return (node.payload for node in self._interval_tree.enumerate())

    def pop_overlapping_chunks(self, chunk):
        return self._interval_tree.pop_overlapping_chunks(chunk)

    def pop_adjacent_chunks(self, chunk):
        return self._interval_tree.pop_adjacent_chunks(chunk)

    def push(self, chunk, skip_checks=False):
        if not skip_checks:
            overlapping_chunks = self._interval_tree.pop_overlapping_chunks(chunk)
            assert not overlapping_chunks
        self._interval_tree.push(chunk)

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

    def random(self):
        raise NotImplementedError("TODO")


def get_next_chunk(chunk_enumerator):
    """ An enumerator wrapper that returns None instead of throwing.

    """
    try:
        return next(chunk_enumerator)
    except StopIteration:
        return None

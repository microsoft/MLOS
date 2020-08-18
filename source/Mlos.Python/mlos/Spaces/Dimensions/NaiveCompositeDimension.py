#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from enum import IntFlag
from numbers import Number

from .ContinuousDimension import ContinuousDimension
from .Dimension import Dimension


class NaiveCompositeDimension(Dimension):
    """ Models a dimension that results from a sequence of union, intersect, and subtract operations.

    For now we just maintain a list of compositions and by doing so we are able to determine if a number
    belongs to this dimension. In principle it is possible to compress the compositions into a canonical
    form and represent this dimension as a union of chunks. This is beneficial and desirable because it
    will allow us to generate numbers from this dimension according to an arbitrary distribution.

    To accomplish this second goal we will use a variant of the interval tree data structure, except we
    will guarantee that no two chunks in the tree overlap (we will simply union such chunks).

    """
    class CompositionType(IntFlag):
        UNION = 0b1
        INTERSECTION = 0b10
        DIFFERENCE = 0b100

    def __init__(self, name, chunks_type, chunks=None):
        super(NaiveCompositeDimension, self).__init__(name=name)

        assert issubclass(chunks_type, Dimension)
        self.chunks_type = chunks_type
        if chunks is None:
            self._compositions = []
        else:
            assert all(isinstance(chunk, chunks_type) for chunk in chunks)
            self._compositions = [(NaiveCompositeDimension.CompositionType.UNION, chunk) for chunk in chunks]

        self._cached_length_lower_bound = None
        self._cached_length_upper_bound = None

    def copy(self):
        copy = NaiveCompositeDimension(name=self.name, chunks_type=self.chunks_type)

        # pylint: disable=protected-access
        copy._compositions = [
            (composition_type, dimension.copy()) for composition_type, dimension in self._compositions
        ]
        return copy

    def __eq__(self, other):
        raise NotImplementedError

    def __len__(self):
        # TODO: we can answer this question precisely once we implement the interval tree. For now let's return
        # the worst case, being the largest set
        _, upper_bound = self.compute_bounds_on_length()
        return upper_bound

    def compute_bounds_on_length(self):
        """ Computes the upper and lower bounds on the length of this dimension.

        :return:
        """
        if self._cached_length_lower_bound is not None and self._cached_length_upper_bound is not None:
            return self._cached_length_lower_bound, self._cached_length_upper_bound

        # we are going to compute the length of all our chunks by iterating over all compositions and adjusting our count
        # accordingly
        length_upper_bound = 0
        length_lower_bound = 0
        for composition_type, dimension in self._compositions:
            if composition_type == NaiveCompositeDimension.CompositionType.UNION:
                length_lower_bound = min(length_lower_bound, len(dimension))
                length_upper_bound += len(dimension)
            elif composition_type == NaiveCompositeDimension.CompositionType.INTERSECTION:
                # the length of the resulting set is at most the smaller of the two and at least 0 if they don't overlap
                length_lower_bound = 0
                length_upper_bound = min(length_upper_bound, len(dimension))
            elif composition_type == NaiveCompositeDimension.CompositionType.DIFFERENCE:
                # the length is at most what it was if there is no overlap and at least the difference between the lengths
                length_lower_bound = max(0, length_lower_bound - len(dimension))
                length_upper_bound = length_upper_bound # unchanged
            else:
                raise ValueError(f"Unrecognized composition type: {composition_type}")
        self._cached_length_lower_bound, self._cached_length_upper_bound = length_lower_bound, length_upper_bound
        return self._cached_length_lower_bound, self._cached_length_upper_bound


    def __contains__(self, item):
        if isinstance(item, Number):
            return self._contains_number(number=item)
        if isinstance(item, Dimension):
            raise NotImplementedError
        raise NotImplementedError

    def __iter__(self):
        # we could brute-force it for now... it's not pretty but it will work
        if self.is_innumerably_large:
            raise RuntimeError("This set is to large to enumerate.")

        # now the fun part - let's enumerate values from all 'UNIONED' chunks and pass them through the the
        # self.__contains__ filter. This is grossly inefficient but we can fix it later
        unioned_dimensions = [
            dimension for composition_type, dimension
            in self._compositions
            if composition_type == NaiveCompositeDimension.CompositionType.UNION
        ]
        already_enumerated_dimensions = []
        for unioned_dimension in unioned_dimensions:
            for value in unioned_dimension:
                if not any(value in dimension for dimension in already_enumerated_dimensions):
                    if value in self:
                        yield value
            already_enumerated_dimensions.append(unioned_dimension)

    def linspace(self, num=100):
        raise NotImplementedError

    def union(self, other):
        assert isinstance(other, self.chunks_type) or (isinstance(other, NaiveCompositeDimension) and other.chunks_type == self.chunks_type)
        union = self.copy()
        union._compositions.append((NaiveCompositeDimension.CompositionType.UNION, other)) # pylint: disable=protected-access
        return union

    def intersection(self, other):
        assert isinstance(other, self.chunks_type) or (isinstance(other, NaiveCompositeDimension) and other.chunks_type == self.chunks_type)
        intersection = self.copy()
        intersection._compositions.append((NaiveCompositeDimension.CompositionType.INTERSECTION, other)) # pylint: disable=protected-access
        return intersection

    def difference(self, other):
        assert isinstance(other, self.chunks_type) or (isinstance(other, NaiveCompositeDimension) and other.chunks_type == self.chunks_type)
        difference = self.copy()
        difference._compositions.append((NaiveCompositeDimension.CompositionType.DIFFERENCE, other)) # pylint: disable=protected-access
        return difference

    def _contains_number(self, number):
        """ Checks if a number belongs to this composite dimension.

        :param number:
        :return:
        """

        # TODO: implement compression
        result = False
        for composition_type, dimension in self._compositions:
            if composition_type == NaiveCompositeDimension.CompositionType.UNION:
                result = result or number in dimension
            elif composition_type == NaiveCompositeDimension.CompositionType.INTERSECTION:
                result = result and number in dimension
            elif composition_type == NaiveCompositeDimension.CompositionType.DIFFERENCE:
                result = result and number not in dimension
            else:
                raise ValueError(f"Unrecognized composition type: {composition_type}")
        return result

    def _contains_discrete_dimension(self, other_dimension):
        self_length_lower_bound, self_length_upper_bound = self.compute_bounds_on_length()
        if len(other_dimension) > self_length_upper_bound:
            # other dimension has more elements than self so self cannot possibly contain it
            return False
        if not other_dimension.is_innumerably_large:
            return all(value in self for value in other_dimension)
        raise NotImplementedError("Determining containment of large sets is not implemented yet.")

    def _contains_categorical_dimension(self, other_dimension):
        if not other_dimension:
            return True
        if other_dimension.is_numeric:
            if other_dimension.is_innumerably_large:
                raise NotImplementedError("Determining containment of large sets is not implemented yet.")
            return all(value in self for value in other_dimension)
        return False

    def _contains_composite_dimension(self, other_dimension):

        _, self_length_upper_bound = self.compute_bounds_on_length()
        if len(other_dimension) > self_length_upper_bound:
            return False

        if self.chunks_type == ContinuousDimension and other_dimension.chunks_type == ContinuousDimension:
            # we would have already compared sizes and if that yielded nothing, we are out of luck until we
            # start maintaining interval trees.
            raise NotImplementedError("Determining containment of large sets is not implemented yet.")

        if other_dimension.is_innumerably_large:
            raise NotImplementedError("Determining containment of large sets is not implemented yet.")

        # if they are enumerable, we could figure it out by brute force
        return all(value in self for value in other_dimension)

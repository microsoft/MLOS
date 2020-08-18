#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from numbers import Number

from .CategoricalDimension import CategoricalDimension
from .EmptyDimension import EmptyDimension


class OrdinalDimension(CategoricalDimension):
    """ A dimension whose values have a total ordering but the distance between consecutive values is unspecified.

    """

    def __init__(self, name, ordered_values=None, ascending=True, random_state=None):
        self.ascending = ascending
        if ordered_values is None:
            ordered_values = []
        super(OrdinalDimension, self).__init__(name=name, values=ordered_values, random_state=random_state)

    def copy(self):
        return OrdinalDimension(
            name=self.name,
            ordered_values=[value for value in self.values],
            ascending=self.ascending
        )

    @property
    def min(self):
        if not self.values:
            return None
        if self.ascending:
            return self.values[0]
        return self.values[-1]

    @property
    def max(self):
        if not self.values:
            return None
        if self.ascending:
            return self.values[-1]
        return self.values[0]

    def _am_i_numeric(self):
        "Determines if all values are numeric."
        all_numeric_so_far = True
        monotonic = True

        # and if it turns out to be numeric, we can check if it is in fact monotonic.. :)
        previous_value = None
        for value in self.values:
            if all_numeric_so_far and not isinstance(value, Number):
                all_numeric_so_far = False
                break
            if previous_value is not None:
                if self.ascending:
                    monotonic = monotonic and (value >= previous_value)
                else:
                    monotonic = monotonic and (value <= previous_value)
            previous_value = value

        if all_numeric_so_far and not monotonic:
            raise RuntimeError(f"The values are not monotonic: {self.values}")
        return all_numeric_so_far

    def intersection_ordinal_dimension(self, other):
        assert isinstance(other, OrdinalDimension)
        assert self.name == other.name
        intersection = OrdinalDimension(
            name=self.name,
            ordered_values=[value for value in self.values if value in other],
            ascending=self.ascending
        )
        if len(intersection) == 0:  # pylint: disable=len-as-condition
            return EmptyDimension(name=self.name, type=OrdinalDimension)
        return intersection

    def union_ordinal_dimension(self, other):
        assert isinstance(other, OrdinalDimension)
        assert self.name == other.name

        if self in other:
            return other.copy()

        if other in self:
            return self.copy()

        # otherwise we create a new OrdinalDimension
        values = [value for value in self.values]
        for value in other:
            if value not in self.values_set:
                values.append(value)
        values = sorted(values, reverse=not self.ascending)

        return OrdinalDimension(name=self.name, ordered_values=values, ascending=self.ascending)

    def difference_ordinal_dimension(self, other):
        assert isinstance(other, OrdinalDimension) and other.name == self.name
        difference = OrdinalDimension(name=self.name, ordered_values=[value for value in self if value not in other], ascending=self.ascending)
        if len(difference) == 0:  # pylint: disable=len-as-condition
            return EmptyDimension(name=self.name, type=OrdinalDimension)
        return difference

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

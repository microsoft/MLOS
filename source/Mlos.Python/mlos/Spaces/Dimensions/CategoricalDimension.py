#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from numbers import Number

from mlos.Spaces.Dimensions.Dimension import Dimension
from mlos.Spaces.Dimensions.EmptyDimension import EmptyDimension


class CategoricalDimension(Dimension):
    """ A dimension whose values are categorical and ordering among them is unspecified.

    """

    def __init__(self, name, values=None, random_state=None):
        super(CategoricalDimension, self).__init__(name=name, random_state=random_state)
        if values is None:
            values = []
        self.values = values
        self.values_set = set(self.values)
        self.is_numeric = self._am_i_numeric()

    def __str__(self):
        return self.to_string()

    def to_string(self, include_name=True):
        values_str = f"{{{', '.join(str(value) for value in self.values[:min(3, len(self))])}{', ...' if len(self) > 3 else ''}}}"
        if include_name:
            return f"{self.name}: {values_str}"
        return values_str

    def __repr__(self):
        return self.to_string(include_name=True)

    def copy(self):
        return CategoricalDimension(
            name=self.name,
            values=[value for value in self.values]
        )

    def __eq__(self, other):
        return isinstance(other, CategoricalDimension) and self.name == other.name and self.values_set == other.values_set

    def __len__(self):
        return len(self.values)

    def __iter__(self):
        for value in self.values:
            yield value

    def __getitem__(self, key):
        return self.values[key]

    def _am_i_numeric(self):
        "Determines if all values are numeric."
        return all(isinstance(value, Number) for value in self.values)

    def __contains__(self, item):
        if isinstance(item, Dimension):
            other_dimension = item
            assert isinstance(item, CategoricalDimension)
            assert self.name == other_dimension.name
            # The only shortcut we have is to compare the lengths
            if len(other_dimension) > len(self):
                return False
            return all(value in self for value in other_dimension)
        return item in self.values_set

    def __and__(self, other):
        return self.intersection(other)

    def __or__(self, other):
        return self.union(other)

    def intersection_categorical_dimension(self, other):
        assert isinstance(other, CategoricalDimension)
        assert self.name == other.name

        intersection = CategoricalDimension(
            name=self.name,
            values=[value for value in self.values if value in other]
        )
        if len(intersection.values) == 0:  # pylint: disable=len-as-condition
            return EmptyDimension(name=self.name, type=CategoricalDimension)
        return intersection

    def union_categorical_dimension(self, other):
        assert isinstance(other, CategoricalDimension)
        assert self.name == other.name

        if self in other:
            return other.copy()
        if other in self:
            return self.copy()

        # otherwise we create a new CategoricalDimension
        values = [value for value in self.values]
        for value in other:
            if value not in self.values_set:
                values.append(value)
        return CategoricalDimension(name=self.name, values=values)

    def difference_categorical_dimension(self, other):
        assert isinstance(other, CategoricalDimension) and self.name == other.name
        return CategoricalDimension(name=self.name, values=[value for value in self if value not in other])

    def linspace(self, num=None):
        return [value for value in self.values]

    def random(self):
        return self._random_state.choice(self.values)

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

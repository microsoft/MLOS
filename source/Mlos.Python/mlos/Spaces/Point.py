#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#

import json

import pandas as pd

from .Dimensions.Dimension import Dimension


class Point:
    """ Models a point in a Hypergrid.

    """
    def __init__(self, **kwargs):
        self.dimension_value_dict = dict()
        for dimension_name, value in kwargs.items():
            self[dimension_name] = value

    def copy(self):
        return Point(**{key: value for key, value in self})

    def flat_copy(self):
        """ Creates a copy of the point but all dimension names are flattened.

        :return:
        """
        flat_dict = {
            Dimension.flatten_dimension_name(dimension_name): value
            for dimension_name, value in self
        }
        return Point(**flat_dict)

    def __eq__(self, other):
        if not isinstance(other, Point):
            return False
        return \
            all(other[dimension_name] == value for dimension_name, value in self) \
            and \
            all(self[dimension_name] == value for dimension_name, value in other)

    def __ne__(self, other):
        return not self == other

    def __iter__(self):
        for dimension_name, value in self.dimension_value_dict.items():
            if not isinstance(value, Point):
                yield dimension_name, value
            else:
                for sub_dimension_name, sub_dimension_value in value:
                    yield dimension_name + "." + sub_dimension_name, sub_dimension_value

    def __getattr__(self, dimension_name):
        return self[dimension_name]

    def __getitem__(self, dimension_name):
        if dimension_name not in self:
            return None
        subgrid_name, dimension_name_without_subgrid_name = Dimension.split_dimension_name(dimension_name)
        if subgrid_name is None:
            return self.dimension_value_dict.get(dimension_name, None)
        return self[subgrid_name][dimension_name_without_subgrid_name]

    def __setitem__(self, dimension_name, value):
        subgrid_name, dimension_name_without_subgrid_name = Dimension.split_dimension_name(dimension_name)
        if subgrid_name is None:
            self.dimension_value_dict[dimension_name] = value
        else:
            point_in_subgrid = self.dimension_value_dict.get(subgrid_name, Point())
            point_in_subgrid[dimension_name_without_subgrid_name] = value
            self.dimension_value_dict[subgrid_name] = point_in_subgrid

    def __contains__(self, dimension_name):
        subgrid_name, dimension_name_without_subgrid_name = Dimension.split_dimension_name(dimension_name)
        if subgrid_name is None:
            return dimension_name in self.dimension_value_dict
        if subgrid_name not in self.dimension_value_dict:
            return False
        return dimension_name_without_subgrid_name in self[subgrid_name]

    def __str__(self):
        return str(self.to_dict())

    def get(self, dimension_name, default):
        value = self[dimension_name]
        return value if value is not None else default

    def to_json(self, indent=None):
        if indent is not None:
            return json.dumps(self.to_dict(), indent=indent)
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str):
        coordinates = json.loads(json_str)
        return Point(**coordinates)

    def to_dict(self):
        return {param_name: value for param_name, value in self}

    def to_pandas(self):
        return pd.DataFrame({param_name: [value] for param_name, value in self})

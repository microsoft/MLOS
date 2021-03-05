#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import json
from numbers import Number

import pandas as pd
from mlos.Spaces.Dimensions.Dimension import Dimension


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
            all(other.get(dimension_name, None) == value for dimension_name, value in self) \
            and \
            all(self.get(dimension_name, None) == value for dimension_name, value in other)

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
        try:
            return self[dimension_name]
        except KeyError:
            pass

        # Raise the exception outside the 'except' block to not make it look like a nested error.
        #
        raise AttributeError(f"This Point does not have a {dimension_name} attribute.")

    def __setattr__(self, name, value):
        if name == "dimension_value_dict":
            self.__dict__[name] = value
        else:
            dimension_name = name
            subgrid_name, dimension_name_without_subgrid_name = Dimension.split_dimension_name(dimension_name)
            if subgrid_name is None:
                self.dimension_value_dict[dimension_name] = value
            else:
                point_in_subgrid = self.dimension_value_dict.get(subgrid_name, Point())
                point_in_subgrid[dimension_name_without_subgrid_name] = value
                self.dimension_value_dict[subgrid_name] = point_in_subgrid

    def __getitem__(self, dimension_name):
        if dimension_name not in self:
            raise KeyError(f"This Point does not have a value along dimension: {dimension_name}")
        subgrid_name, dimension_name_without_subgrid_name = Dimension.split_dimension_name(dimension_name)
        if subgrid_name is None:
            return self.dimension_value_dict[dimension_name]
        return self[subgrid_name][dimension_name_without_subgrid_name]

    def get(self, dimension_name, default=None):
        try:
            return self[dimension_name]
        except KeyError:
            return default

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

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return str(self.to_json(indent=2))

    def __getstate__(self):
        return self.to_json()

    def __setstate__(self, state):
        temp_point = self.from_json(state)
        self.dimension_value_dict = temp_point.dimension_value_dict

    def to_json(self, indent=None):
        if indent is not None:
            return json.dumps(self.to_dict(), indent=indent)
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str):
        coordinates = json.loads(json_str)
        return Point(**coordinates)

    def to_dict(self):
        return_dict = {}
        for param_name, value in self:
            if isinstance(value, Number) and int(value) == value and not isinstance(value, bool):
                value = int(value)
            return_dict[param_name] = value
        return return_dict

    def to_dataframe(self):
        return pd.DataFrame({param_name: [value] for param_name, value in self})

    @classmethod
    def from_dataframe(cls, dataframe: pd.DataFrame):
        assert len(dataframe.index) == 1
        dataframe = dataframe.dropna(axis=1)
        dataframe_dict = dataframe.to_dict(orient='list')
        point_dict = {key: values[0] for key, values in dataframe_dict.items()}
        return Point(**point_dict)

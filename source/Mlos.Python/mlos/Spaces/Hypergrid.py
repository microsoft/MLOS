#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from abc import ABC, abstractmethod
import random
import pandas as pd
from mlos.Spaces.Dimensions.ContinuousDimension import ContinuousDimension
from mlos.Spaces.Dimensions.CategoricalDimension import CategoricalDimension
from mlos.Spaces.Dimensions.Dimension import Dimension
from mlos.Spaces.Dimensions.DiscreteDimension import DiscreteDimension
from mlos.Spaces.Point import Point
from mlos.Tracer import trace


class Hypergrid(ABC):
    """A base class for all search-space-like classes.

    """

    def __init__(self, name=None, random_state=None):
        self.name = name
        if random_state is None:
            random_state = random.Random()
        self._random_state = random_state

    @property
    def dimension_names(self):
        return [dimension.name for dimension in self.dimensions]

    @abstractmethod
    def __contains__(self, item):
        raise NotImplementedError("All subclasses must implement this.")

    @abstractmethod
    def __getitem__(self, item):
        raise NotImplementedError

    @property
    @abstractmethod
    def random_state(self):
        return self._random_state

    @random_state.setter
    @abstractmethod
    def random_state(self, value):
        raise NotImplementedError("This has to be implemented in all derived classes to set random_state on individual dimensions.")

    @property
    @abstractmethod
    def dimensions(self):
        raise NotImplementedError("All subclasses must implement this.")

    @abstractmethod
    def get_dimensions_for_point(self, point, return_join_dimensions=True):
        raise NotImplementedError("All subclasses must implement this.")

    @abstractmethod
    def random(self, point=None):
        raise NotImplementedError("All subclasses must implement this.")

    @trace()
    def random_dataframe(self, num_samples):
        config_dicts = [
            self.random().to_dict()
            for _ in range(num_samples)
        ]
        return pd.DataFrame(config_dicts)

    @trace()
    def get_valid_rows_index(self, original_dataframe) -> pd.Index:
        """Returns an index of all rows in the dataframe that belong to this Hypergrid.

        Valid rows are rows with no NaNs and with values for all dimensions in the required ranges.

        :param df:
        :return:
        """
        assert set(original_dataframe.columns.values).issuperset(set(self.dimension_names))

        valid_rows_index = None
        dataframe = original_dataframe[self.dimension_names]

        if not self.is_hierarchical():
            # Let's exclude any extra columns
            #
            valid_rows_index = dataframe.index[dataframe.notnull().all(axis=1)]

            # Now for each column let's filter out the rows whose values are outside the allowed ranges.
            #
            for dimension in self.dimensions:
                if isinstance(dimension, ContinuousDimension):
                    if dimension.include_min:
                        valid_rows_index = valid_rows_index.intersection(dataframe[dataframe[dimension.name] >= dimension.min].index)
                    else:
                        valid_rows_index = valid_rows_index.intersection(dataframe[dataframe[dimension.name] > dimension.min].index)

                    if dimension.include_max:
                        valid_rows_index = valid_rows_index.intersection(dataframe[dataframe[dimension.name] <= dimension.max].index)
                    else:
                        valid_rows_index = valid_rows_index.intersection(dataframe[dataframe[dimension.name] < dimension.max].index)

                elif isinstance(dimension, DiscreteDimension):
                    valid_rows_index = valid_rows_index.intersection(dataframe[dataframe[dimension.name] >= dimension.min].index)
                    valid_rows_index = valid_rows_index.intersection(dataframe[dataframe[dimension.name] <= dimension.max].index)

                elif isinstance(dimension, CategoricalDimension):
                    valid_rows_index = valid_rows_index.intersection(dataframe[dataframe[dimension.name].isin(dimension.values_set)].index)

                else:
                    raise ValueError(f"Unsupported dimension type: {type(dimension)}")

        else:
            # TODO: this can be optimized. Do everything we did for non-hierarchical hypergrids, but also evaluate constraints imposed by join dimensions.
            #
            valid_rows_index = dataframe[dataframe.apply(
                lambda row: Point(**{dim_name: row[i] for i, dim_name in enumerate(self.dimension_names)}) in self,
                axis=1
            )].index

        return valid_rows_index

    @trace()
    def filter_out_invalid_rows(self, original_dataframe: pd.DataFrame, exclude_extra_columns=True) -> pd.DataFrame:
        """Returns a dataframe containing only valid rows from the original_dataframe.

        Valid rows are rows with no NaNs and with values for all dimensions in the required ranges.
        If there are additional columns, they will be dropped unless exclude_extra_columns == False.
        """
        valid_rows_index = self.get_valid_rows_index(original_dataframe)
        assert len(valid_rows_index) <= len(original_dataframe.index)

        if exclude_extra_columns:
            return original_dataframe.loc[valid_rows_index, self.dimension_names]
        return original_dataframe.loc[valid_rows_index]


    @abstractmethod
    def join(self, subgrid, on_external_dimension: Dimension):
        raise NotImplementedError("All subclasses must implement this.")

    @abstractmethod
    def is_hierarchical(self):
        raise NotImplementedError("All subclasses must implement this.")

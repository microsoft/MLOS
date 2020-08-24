#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import numpy as np

from mlos.Exceptions import InvalidDimensionException
from mlos.Spaces import ContinuousDimension, DiscreteDimension, CategoricalDimension

class Heatmap:
    """ A single heatmap for an artist to draw.

    """
    DEFAULT_NUM_TICKS = 5
    MAX_NUM_TICKS = 10

    def __init__(self, x_dimension, y_dimension, x_resolution, y_resolution):
        self.x_dimension = x_dimension
        self.y_dimension = y_dimension
        self.x_resolution = x_resolution
        self.y_resolution = y_resolution

        self.x_ticks, self.x_tick_labels = self._get_ticks_and_labels(dimension=x_dimension, resolution=x_resolution)
        self.y_ticks, self.y_tick_labels = self._get_ticks_and_labels(dimension=y_dimension, resolution=y_resolution)

        self.title = f"{self.y_name} vs. {self.x_name}"

        # Preallocate the values array to later fill with predicted values.
        #
        self.values = np.zeros((self.x_resolution, self.y_resolution))
        self.min_value = 0
        self.max_value = 0

    @property
    def x_name(self):
        return self.x_dimension.name

    @property
    def y_name(self):
        return self.y_dimension.name

    def set_values_to_zero(self):
        self.values = np.zeros((self.x_resolution, self.y_resolution))

    def update_values(self, new_values):
        """ Updates self.values to reflect the new values.

        The complication here is that new_values could potentially be a smaller matrix than self.values. In such
        a case we must "scale" the matrix to fill in the desired resolution.

        :param new_values:
        :return:
        """
        new_values = np.nan_to_num(x=new_values, copy=False, nan=0)
        num_new_rows = new_values.shape[0]
        num_new_cols = new_values.shape[1]

        assert num_new_rows <= self.y_resolution and num_new_cols <= self.x_resolution

        if num_new_rows == self.y_resolution and num_new_cols == self.x_resolution:
            # we can just assign
            self.values = new_values
            return

        starting_row = 0
        for row in range(num_new_rows):
            ending_row = round(self.y_resolution * (row + 1) / num_new_rows)
            starting_col = 0
            for col in range(num_new_cols):
                ending_col = round(self.x_resolution * (col + 1) / num_new_cols)
                self.values[starting_row:ending_row:1, starting_col:ending_col:1] = new_values[row, col]
                starting_col = ending_col
            starting_row = ending_row
        return

    def _get_ticks_and_labels(self, dimension, resolution):
        if isinstance(dimension, ContinuousDimension):
            ticks = np.linspace(0, resolution, self.DEFAULT_NUM_TICKS)
            tick_labels = np.linspace(dimension.min, dimension.max, self.DEFAULT_NUM_TICKS)
        elif isinstance(dimension, DiscreteDimension):
            num_ticks = min(len(dimension), self.MAX_NUM_TICKS)
            ticks = np.linspace(0, resolution, num_ticks)
            tick_labels = dimension.linspace(num=num_ticks)
        elif isinstance(dimension, CategoricalDimension):
            # We insert some empty tick labels to align the actual labels with centers of their respective buckets.
            #
            num_ticks = len(dimension) * 2 + 1
            ticks = np.linspace(0, resolution, num_ticks)
            tick_labels = ['' for _ in range(num_ticks)]
            for i, value in enumerate(dimension.values):
                tick_labels[i * 2 + 1] = value
        else:
            raise InvalidDimensionException()

        return ticks, tick_labels

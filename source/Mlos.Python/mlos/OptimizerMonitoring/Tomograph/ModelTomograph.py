#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from mlos.Optimizers.OptimizerBase import OptimizerBase
from mlos.Optimizers.RegressionModels.Prediction import Prediction
from mlos.Spaces import Point
from mlos.OptimizerMonitoring.Tomograph.Heatmap import Heatmap

class ModelTomograph:
    """ The role of this class is to present to the user the grid-of-heatmaps view of the internal state of
    a model over time.

    Grid-of-heatmaps is a way of visualizing many dimensional spaces by producing a series of 2-Dimensional
    heatmaps depicting the state of the model along any two dimensions.

    """
    DEFAULT_RESOLUTION = 100

    def __init__(
            self,
            optimizer: OptimizerBase,
            resolution: int = DEFAULT_RESOLUTION,
            dimension_names_to_skip=None, # TODO: remove - add an adapter that always removes useless dimension names.
            figure_size=(10, 10)
    ):
        """ Draws a grid of heat maps depicting the internal state of the bayesian optimizer's surrogate model.

        Each pixel in each heatmap represents a prediction. Each heatmap represents a cross-section of the feature-space that contains a specific point
        (usually the optimum, or the last observed sample). So the prediction in each pixel is made for a tuple consisting of:
        1. a value from a linspace along the x-dimension (different for every column in the heatmap)
        2. a value from a linspace along the y-dimension (different for every row in the heatmap)
        3. a value for every other dimension (taken from the point, same for all pixels in a given heatmap)

        From earlier prototypes we know that to draw a heatmap we need:
            1) a linspace of values along the x-dimension
            2) a linspace of values along the y-dimension
            3) for each dimension different from the x-dimension and from the y-dimension: a list containing the coordinate of the point along that dimension

        We can then create a meshgrid of 1,2, and 3, convert it to a dataframe and send to the Optimizer.predict() function. Right now, I intend to only
        implement the plot of the predicted value but here are some possible extensions:
            1) Plot the utility function value to understand how new suggestions are obtained (especially useful when combined with 4)
            2) Plot all previous observations as points atop the heatmap - this should show us how the model relates to data (useful when combined with 3)
            3) Plot uncertainty (perhaps by varying opacity).
            4) Plot all of the utility function values evaluated to produce the latest suggestion - would show us if the utility function optimizer
                is missing some important sectors of the search space.


        :param optimizer: a reference to an object implementing the OptimizerBase.
        :param resolution: maximum number of pixels along a dimension of each heatmap.
        :param dimension_names_to_skip: dimensions not to be plotted. Remove this. Consider a solution, where mutually exclusive subgrids are plotted on
                separate figures.
        :param figure_size: a 2-tuple determining the size of the figure according to matplotlib rules.
        """
        self.optimizer = optimizer
        feature_space = optimizer.optimization_problem.parameter_space # TODO: make this feature_space
        self.ordered_dim_names = [dimension.name for dimension in feature_space.dimensions]
        self.ordered_linspaces = [dimension.linspace(num=resolution) for dimension in feature_space.dimensions]
        self.linspaces_by_name = {name: linspace for name, linspace in zip(self.ordered_dim_names, self.ordered_linspaces)}
        self.dimension_names_to_skip = dimension_names_to_skip if dimension_names_to_skip is not None else {'contains_parameters', 'contains_context'}

        self.plottable_dimensions = [dimension for dimension in feature_space.dimensions if dimension.name not in self.dimension_names_to_skip]
        self.num_plottable_dimensions = len(self.plottable_dimensions)
        self.resolution = resolution

        self.known_objective_value_min = None
        self.known_objective_value_max = None

        # Let's construct all heatmaps that we will need.
        #
        self._heatmaps_grid = [[None for col in range(self.num_plottable_dimensions)] for row in range(self.num_plottable_dimensions)]
        for col, x_dim in enumerate(self.plottable_dimensions):
            for row, y_dim in enumerate(self.plottable_dimensions):
                self._heatmaps_grid[row][col] = Heatmap(
                    x_dimension=x_dim,
                    y_dimension=y_dim,
                    x_resolution=self.resolution,
                    y_resolution=self.resolution
                )

        self._figure_size = figure_size
        self._figure = None
        self._axes = None

    def plot(self, point=None, time=None, objective_name=None):
        """ Plots a grid of 2D cross sections of the models' view of the search space.

        :param point: The point contained by all 2D cross sections.
        :return:
        """

        if point is None:
            point = self.optimizer.optimization_problem.parameter_space.random()
            print(point)

        self._create_figure_and_axes()
        self._update_heatmaps(point, time, objective_name)
        for axes_row, heatmap_row in zip(self._axes, self._heatmaps_grid):
            for axes, heatmap in zip(axes_row, heatmap_row):
                axes.clear()
                axes.set_xticks([])
                axes.set_yticks([])
                axes.imshow(heatmap.values, cmap='RdBu', interpolation='nearest', vmin=self.known_objective_value_min, vmax=self.known_objective_value_max)

        for axes, heatmap in zip(self._axes[-1][:-1], self._heatmaps_grid[-1][:-1]):
            axes.set_xlabel(heatmap.x_name, rotation=90, verticalalignment='top')
            axes.set_xticks(heatmap.x_ticks)
            axes.set_xticklabels(heatmap.x_tick_labels, rotation=90)

        # The label and ticks for the last column has to be set separately.
        #
        axes = self._axes[-1][-1]
        heatmap = self._heatmaps_grid[-1][-2]
        name = self._heatmaps_grid[-1][-1].x_name
        axes.set_xlabel(name, rotation=90, verticalalignment='top')
        axes.set_xticks(heatmap.x_ticks)
        axes.set_xticklabels(heatmap.x_tick_labels, rotation=90)

        for axes_row, heatmap_row in zip(self._axes[1:], self._heatmaps_grid[1:]):
            axes = axes_row[0]
            heatmap = heatmap_row[0]
            axes.set_ylabel(heatmap.y_name, rotation=0, horizontalalignment='right')
            axes.set_yticks(heatmap.y_ticks)
            axes.set_yticklabels(heatmap.y_tick_labels)

        # The label and ticks for the first row has to be set separately.
        #
        axes = self._axes[0][0]
        heatmap = self._heatmaps_grid[0][1]
        axes.set_ylabel(heatmap.y_name, rotation=0, horizontalalignment='right')
        axes.set_yticks(heatmap.y_ticks)
        axes.set_yticklabels(heatmap.y_tick_labels)

        self._figure.canvas.draw()
        plt.show()



    def _update_heatmaps(self, point: Point, time: int, objective_name: str):

        # We need to construct a meshgrid for every heatmap. We do this by getting the linspaces for the
        # x_dimension and y_dimension. For the other dimensions, we create a linspace containing a single value
        # point[dim_name]. When we combine these linspaces into a meshgrid we get a tuple for each pixel.
        #
        for col, x_dim in enumerate(self.plottable_dimensions):
            for row, y_dim in enumerate(self.plottable_dimensions):

                if x_dim.name not in point or y_dim.name not in point:
                    # The point does not belong to the plane depicted by this heatmap.
                    #
                    self._heatmaps_grid[row][col].set_values_to_zero()
                    continue

                if row == col:
                    # For now on the diagonal we just plot empty grids.
                    # TODO: we could be plotting graphs of objective value vs x-dimension.
                    continue

                if col > row:
                    # TODO: We can just transpose the already computed heatmap from below the diagonal.
                    #
                    pass



                # TODO: these can be computed in the constructor
                #
                x_dim_linspace = self.linspaces_by_name[x_dim.name]
                y_dim_linspace = self.linspaces_by_name[y_dim.name]

                # If current_x_resolution < self.x_resolution or current_y_resolution < self.y_resolution we still need to create an image with
                # self.x_resolution * self.y_resolution pixels. But we should create the smallest query to the optimizer possible. The approach
                # we take here is to create a query for current_x_resolution * current_y_resolution pixels, and then use Kronecker product to
                # "scale" the heatmap up to self.x_resolution * self.y_resolution pixels.
                #
                current_x_resolution = len(x_dim_linspace)
                current_y_resolution = len(y_dim_linspace)

                features_df = self._create_features_dataframe(x_dim, y_dim, point)
                predictions = self.optimizer.predict(parameter_values_pandas_frame=features_df, t=time, objective_name=objective_name)
                predictions.add_invalid_rows_at_missing_indices(desired_index=features_df.index)
                predictions_df = predictions.get_dataframe()
                if not predictions_df.empty and predictions_df[Prediction.LegalColumnNames.IS_VALID_INPUT.value].any():
                    predicted_mean = predictions_df[Prediction.LegalColumnNames.PREDICTED_VALUE.value].to_numpy()

                    # To plot the values we need to reshape them back to the resolution.
                    #
                    reshaped_mean = predicted_mean.reshape((current_y_resolution, current_x_resolution))

                    self._heatmaps_grid[row][col].update_values(new_values=reshaped_mean)

                    # Lastly: remember min and max for plotting
                    #
                    self._update_known_extremes(current_min=np.min(predicted_mean), current_max=np.max(predicted_mean))

    def _create_figure_and_axes(self):
        self._figure, self._axes = plt.subplots(
            nrows=self.num_plottable_dimensions,
            ncols=self.num_plottable_dimensions,
            figsize=self._figure_size
        )
        if self.num_plottable_dimensions == 1:
            self._axes = [[self._axes]]

    def _create_features_dataframe(self, x_dim, y_dim, point):
        """ Creates a dataframe where each row corresponds to one pixel in the heatmap.

        The dataframe contains the cross product of x_dim and y_dim linspaces, extended with fixed values
        for all other dimensions.

        :param x_dim:
        :param y_dim:
        :param point:
        :return:
        """
        linspaces = [self.linspaces_by_name[x_dim.name], self.linspaces_by_name[y_dim.name]]
        dim_names = [x_dim.name, y_dim.name]
        for dim_name in self.ordered_dim_names:
            if dim_name in (x_dim.name, y_dim.name):
                continue
            else:
                linspaces.append([point[dim_name] if dim_name in point else [np.NaN]])
                dim_names.append(dim_name)

        # We now create (x_resolution * y_resolution) tuples but shaped into a multi-dimensional grid.
        #
        meshgrids = np.meshgrid(*linspaces)

        # To convert it into a dataframe, we need to reshape them into a collection of columns.
        #
        reshaped_meshgrids = [meshgrid.reshape(-1) for meshgrid in meshgrids]

        # Finally build the dataframe.
        #
        meshgrids_dict = {dim_name: meshgrid for dim_name, meshgrid in zip(dim_names, reshaped_meshgrids)}
        pandas_df = pd.DataFrame(meshgrids_dict)
        return pandas_df

    def _update_known_extremes(self, current_min, current_max):
        if self.known_objective_value_min is None or self.known_objective_value_min > current_min:
            self.known_objective_value_min = current_min

        if self.known_objective_value_max is None or self.known_objective_value_max < current_max:
            self.known_objective_value_max = current_max

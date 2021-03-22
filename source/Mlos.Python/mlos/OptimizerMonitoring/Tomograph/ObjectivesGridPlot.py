#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from bokeh.layouts import gridplot, column
from bokeh.models import Div, HoverTool
from bokeh.plotting import figure

from mlos.Logger import create_logger
from mlos.Optimizers.OptimizationProblem import OptimizationProblem
from mlos.OptimizerMonitoring.Tomograph.ObservationsDataSource import ObservationsDataSource
from mlos.Spaces.HypergridAdapters import CategoricalToDiscreteHypergridAdapter


class ObjectivesGridPlot:
    """Maintains all data and metadata to produce the grid plot in the objective space.
    """

    def __init__(
            self,
            optimization_problem: OptimizationProblem,
            observations_data_source: ObservationsDataSource,
            logger=None
    ):
        if logger is None:
            logger = create_logger(self.__class__.__name__)
        self.logger = logger

        # The data source is maintained by the tomograph.
        #
        self._observations_data_source = observations_data_source


        # Metatdata - what dimensions are we going to be plotting here?
        #
        self.optimization_problem = optimization_problem
        self.num_objectives = len(optimization_problem.objective_space.dimension_names)
        self.objective_names = optimization_problem.objective_space.dimension_names
        self._feature_space_adapter = CategoricalToDiscreteHypergridAdapter(adaptee=self.optimization_problem.feature_space)


        # Stores figure ranges by name so that we can synchronize zooming and panning
        #
        self._x_ranges_by_name = {}
        self._y_ranges_by_name = {}


        # Stores an array of all plots for all objectives.
        #
        self._figures = [
            [None for col in range(self.num_objectives)]
            for row in range(self.num_objectives)
        ]

        self._title = Div(text="<h1>Objectives</h1>")

        # Stores the bokeh gridplot object.
        #
        self._grid_plot = None

    @property
    def formatted_plots(self):
        return column([self._title, self._grid_plot])

    def update_plots(self):
        """Updates the plot with observations from data source.
        """

        self._x_ranges_by_name = {}
        self._y_ranges_by_name = {}
        self._grid_plot = None

        tooltips = [(f"{feature_name}", f"@{feature_name}") for feature_name in self._feature_space_adapter.dimension_names]
        tooltips.extend([(f"{objective_name}", f"@{objective_name}") for objective_name in self.optimization_problem.objective_names])
        hover = HoverTool(tooltips=tooltips)

        plot_options = dict(
            plot_width=int(2000 / self.num_objectives),
            plot_height=int(2000 / self.num_objectives),
            tools=['box_select', 'lasso_select', 'box_zoom', 'wheel_zoom', 'reset', hover]
        )

        for row, row_dimension_name in enumerate(self.objective_names):
            for col, col_dimension_name in enumerate(self.objective_names):

                x_axis_name = col_dimension_name
                y_axis_name = row_dimension_name

                if row == col:
                    # For plots on the diagonals, we want to plot the is_pareto vs. objective
                    #
                    x_axis_name = 'is_pareto'

                fig = figure(**plot_options)

                fig.scatter(
                    x_axis_name,
                    y_axis_name,
                    marker='circle',
                    source=self._observations_data_source.data_source
                )

                fig.xaxis.axis_label = x_axis_name
                fig.yaxis.axis_label = y_axis_name

                if row == col:
                    fig.xaxis.ticker = [0, 1]
                    fig.xaxis.major_label_overrides = {0: 'Dominated', 1: 'Pareto'}

                self._set_ranges(fig, x_axis_name, y_axis_name)
                self._figures[row][col] = fig

        self._grid_plot = gridplot(self._figures)


    def _set_ranges(self, fig, x_axis_name, y_axis_name):
        """Sets the ranges on each axis to enable synchronized panning and zooming.

        Basically, when we see a given range name for the first time we cache the range and set that cached range for all figures
        in the future. This way all plots that share the same range name (so the same dimension) are synchronized for panning and
        zooming.
        """
        if x_axis_name in self._x_ranges_by_name:
            fig.x_range = self._x_ranges_by_name[x_axis_name]
        else:
            self._x_ranges_by_name[x_axis_name] = fig.x_range

        if y_axis_name in self._y_ranges_by_name:
            fig.y_range = self._y_ranges_by_name[y_axis_name]
        else:
            self._y_ranges_by_name[y_axis_name] = fig.y_range

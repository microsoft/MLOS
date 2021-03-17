#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from typing import List

from bokeh.layouts import gridplot, column
from bokeh.models import ColorBar, Div, HoverTool, LinearColorMapper
from bokeh.plotting import figure

import pandas as pd

from mlos.Logger import create_logger
from mlos.Optimizers.OptimizationProblem import OptimizationProblem
from mlos.OptimizerMonitoring.Tomograph.ObservationsDataSource import ObservationsDataSource
from mlos.Spaces.HypergridAdapters import CategoricalToDiscreteHypergridAdapter


class GridPlot:
    """Maintains all data, meta-data and styling information required to produce a grid-plot.

    The grid plot is built based on the OptimizationProblem instance, to find out what objectives and what
    features are to be plotted. We use information contained in the dimensions to compute the ranges for all
    axes/ranges on the plot, as well as to configure the color map.

    If the range is infinite (as can be the case with many objectives) we can use the observed range of values to
    configure the range of values to be plotted.

    Each figure in the grid plot contains:
    * Either a scatter plot of feature vs. feature where the color of each point corresponds to the objective value
    * Or a scatter plot of feature vs. objective (if we are on a diagonal).

    Additionally, we could also plot the predicted values as a background heatmap for the feature vs. feature
    plots, and a predicted value with confidence intervals plot for feature vs. objective plots. This of course introduces a complication
    of needing to query the optimizer for each pixel and so we will add it later.
    """

    def __init__(
        self,
        optimization_problem: OptimizationProblem,
        objective_name: str,
        observations_data_source: ObservationsDataSource,
        logger=None
    ):
        if logger is None:
            logger = create_logger(self.__class__.__name__)
        self.logger = logger

        # The data source is maintained by the tomograph.
        #
        self._observations_data_source = observations_data_source

        #  Metatdata - what dimensions are we going to be plotting here?
        #
        self.optimization_problem = optimization_problem
        assert objective_name in self.optimization_problem.objective_names
        self.objective_name = objective_name

        # The adapter is needed if we want to create plots of categorical dimensions. It maps categorical values to integers so
        # that we can consistently place them on the plots.
        #
        self._feature_space_adapter = CategoricalToDiscreteHypergridAdapter(adaptee=self.optimization_problem.feature_space)

        self.feature_dimension_names: List[str] = [
            feature_name
            for feature_name
            in self._feature_space_adapter.dimension_names
            if feature_name != "contains_context"
        ]
        self.num_features = len(self.feature_dimension_names)

        # Stores figure ranges by name so that we can synchronize zooming and panning
        #
        self._x_ranges_by_name = {}
        self._y_ranges_by_name = {}

        # Stores an array of all plots for all objectives.
        #
        self._figures = [
            [None for col in range(self.num_features)]
            for row in range(self.num_features)
        ]

        self._title = Div(text=f"<h1>{self.objective_name}</h1>")

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

        tooltips = [(f"{feature_name}", f"@{feature_name}") for feature_name in self.feature_dimension_names]
        tooltips.extend([(f"{objective_name}", f"@{objective_name}") for objective_name in self.optimization_problem.objective_names])
        hover = HoverTool(tooltips=tooltips)

        plot_options = dict(
            plot_width=int(2000 / self.num_features),
            plot_height=int(2000 / self.num_features),
            tools=['box_select', 'lasso_select', 'box_zoom', 'wheel_zoom', 'reset', hover]
        )

        final_column_plot_options = dict(
            plot_width=int(2000 / self.num_features) + 75,
            plot_height=int(2000 / self.num_features),
            tools=['box_select', 'lasso_select', 'box_zoom', 'wheel_zoom', 'reset', hover]
        )

        color_mapper = LinearColorMapper(
            palette='Turbo256',
            low=self._observations_data_source.observations_df[self.objective_name].min(),
            high=self._observations_data_source.observations_df[self.objective_name].max()
        )

        for row, row_dimension_name in enumerate(self.feature_dimension_names):
            for col, col_dimension_name in enumerate(self.feature_dimension_names):

                x_axis_name = col_dimension_name
                x_ticks, x_tick_label_mapping = self._get_feature_ticks_and_tick_label_mapping(x_axis_name)

                if row == col:
                    # For plots on the diagonals, we want to plot the row dimension vs. objective
                    #
                    y_axis_name = self.objective_name

                    # Since objectives are always continuous, the default ticks and tick-labels provided by bokeh work well.
                    #
                    y_ticks, y_tick_label_mapping = None, None
                else:
                    y_axis_name = row_dimension_name
                    y_ticks, y_tick_label_mapping = self._get_feature_ticks_and_tick_label_mapping(y_axis_name)

                if col == (self.num_features - 1):
                    fig = figure(**final_column_plot_options)
                else:
                    fig = figure(**plot_options)

                fig.scatter(
                    x_axis_name,
                    y_axis_name,
                    color={'field': self.objective_name, 'transform': color_mapper},
                    marker='circle',
                    source=self._observations_data_source.dominated_data_source,
                    legend_label="dominated",
                    muted_alpha=0.02 # TODO: figure out how to have clicking on the legend mute unselected points.
                )

                fig.scatter(
                    x_axis_name,
                    y_axis_name,
                    color={'field': self.objective_name, 'transform': color_mapper},
                    marker='triangle',
                    source=self._observations_data_source.pareto_data_source,
                    legend_label="pareto optimal",
                    muted_alpha=0.02 # TODO: figure out how to have clicking on the legend mute unselected points.
                )

                fig.legend.click_policy="hide"
                fig.xaxis.axis_label = x_axis_name
                fig.yaxis.axis_label = y_axis_name


                fig.xaxis.ticker = x_ticks
                fig.axis.major_label_overrides = x_tick_label_mapping

                if y_ticks is not None:
                    fig.yaxis.ticker = y_ticks
                    fig.yaxis.major_label_overrides = y_tick_label_mapping

                self._set_ranges(fig, x_axis_name, y_axis_name)

                self.logger.debug(f"Assigning figure to [{row}][{col}]. {self.objective_name}, {row_dimension_name}, {col_dimension_name}")
                self._figures[row][col] = fig

            color_bar = ColorBar(color_mapper=color_mapper, label_standoff=12, location=(0,0), title=self.objective_name)
            self._figures[row][-1].add_layout(color_bar, 'right')

        self._grid_plot = gridplot(self._figures)


    def _get_feature_ticks_and_tick_label_mapping(self, axis_name):
        """Returns tick positions as well as labels for each tick.

        The complication is that tick labels can be categorical, but ticks must be plotted at locations specified by integers.

        Once again adapters come to the rescue: we simply use an adapter to construct a (persistent) mapping between the categorical
        values (needed to label the ticks) and integer values (needed to position the ticks). This mapping is persisted in the
        adapter and here we dole it out to each plot on an as-needed basis.

        :param axis_name:
        :return:
        """
        projected_ticks = self._feature_space_adapter[axis_name].linspace(5)
        projected_ticks_df = pd.DataFrame({axis_name: projected_ticks})
        unprojected_ticks_df = self._feature_space_adapter.unproject_dataframe(projected_ticks_df)
        unprojected_col_name = unprojected_ticks_df.columns[0]
        tick_mapping = {
            projected_tick: f"{unprojected_tick:.2f}" if isinstance(unprojected_tick, float) else str(unprojected_tick)
            for projected_tick, unprojected_tick
            in zip(projected_ticks, unprojected_ticks_df[unprojected_col_name])
        }
        return projected_ticks, tick_mapping


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

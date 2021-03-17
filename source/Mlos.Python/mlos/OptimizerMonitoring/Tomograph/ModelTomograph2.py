#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from typing import List

from bokeh.layouts import column

from mlos.Logger import create_logger
from mlos.Optimizers.OptimizerBase import OptimizerBase
from mlos.OptimizerMonitoring.Tomograph.GridPlot import GridPlot
from mlos.OptimizerMonitoring.Tomograph.ObservationsDataSource import ObservationsDataSource

class ModelTomograph2:
    """Upgraded version of the Tomograph.

    The goal is to make the Tomograph present more data in a more interactive way than the first version.

    So far the ModelTomograph2 class is capable of producing a grid-plot of scatter-plots for all of the observations.

    TODO
    In the future it will be built up to also show the heatmaps (at which point we can retire the original Tomograph), 3D visualizations
    of interactions, pareto frontier plots, etc.

    """


    def __init__(self, optimizer: OptimizerBase, logger=None):
        if logger is None:
            logger = create_logger(self.__class__.__name__)
        self.logger = logger

        self.optimizer = optimizer
        self.optimization_problem = optimizer.optimization_problem

        params_df, objectives_df, context_df = self.optimizer.get_all_observations()
        pareto_df = self.optimizer.pareto_frontier.pareto_df

        self.bokeh_observations_data_source = ObservationsDataSource(
            optimization_problem=self.optimization_problem,
            parameters_df=params_df,
            context_df=context_df,
            objectives_df=objectives_df,
            pareto_df=pareto_df
        )

    def get_observations_plot(self, objective_names: List[str] = None, refresh_data: bool = True):
        """Plot all observations.
        """

        if objective_names is None:
            objective_names = self.optimization_problem.objective_names

        self.logger.debug(f"Producing observations plot for objectives: {objective_names}")

        if refresh_data:
            params_df, objectives_df, context_df = self.optimizer.get_all_observations()
            pareto_df = self.optimizer.pareto_frontier.pareto_df
            self.bokeh_observations_data_source.update_data(parameters_df=params_df, context_df=context_df, objectives_df=objectives_df, pareto_df=pareto_df)

        plots = []
        for objective_name in objective_names:
            grid_plot = GridPlot(
                optimization_problem=self.optimization_problem,
                objective_name=objective_name,
                observations_data_source=self.bokeh_observations_data_source,
                logger=self.logger
            )
            grid_plot.update_plots()
            plots.append(grid_plot.formatted_plots)

        return column(plots)

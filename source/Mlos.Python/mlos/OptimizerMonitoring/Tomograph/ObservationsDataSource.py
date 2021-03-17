#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from bokeh.models import ColumnDataSource

import pandas as pd

from mlos.Optimizers.OptimizationProblem import OptimizationProblem
from mlos.Spaces.HypergridAdapters import CategoricalToDiscreteHypergridAdapter


class ObservationsDataSource:
    """Maintains data source that the individual GridPlots can use.
    """
    def __init__(
        self,
        optimization_problem: OptimizationProblem,
        parameters_df: pd.DataFrame,
        context_df: pd.DataFrame,
        objectives_df: pd.DataFrame,
        pareto_df: pd.DataFrame
    ):
        self.optimization_problem = optimization_problem
        self._feature_space_adapter = CategoricalToDiscreteHypergridAdapter(adaptee=self.optimization_problem.feature_space)

        self.parameters_df: pd.DataFrame = None
        self.context_df: pd.DataFrame = None
        self.objectives_df: pd.DataFrame = None
        self.pareto_df: pd.DataFrame = None
        self.observations_df: pd.DataFrame = None

        self.data_source: ColumnDataSource = None
        self.pareto_data_source: ColumnDataSource = None
        self.dominated_data_source: ColumnDataSource = None


        self.data_source = ColumnDataSource()
        self.pareto_data_source = ColumnDataSource()
        self.dominated_data_source = ColumnDataSource()

        self.update_data(parameters_df=parameters_df, context_df=context_df, objectives_df=objectives_df, pareto_df=pareto_df)

    def update_data(self, parameters_df: pd.DataFrame, context_df: pd.DataFrame, objectives_df: pd.DataFrame, pareto_df: pd.DataFrame):
        self.parameters_df = parameters_df
        self.context_df = context_df
        self.objectives_df = objectives_df
        self.pareto_df = pareto_df
        self.observations_df = self._construct_observations()

        # In order to preserve the identity of the data sources, we create temporary ones, and then copy their data over to the data
        # sources in use by the grid plots.
        #
        temp_data_source = ColumnDataSource(data=self.observations_df)
        temp_pareto_data_source = ColumnDataSource(data=self.observations_df[self.observations_df['is_pareto']])
        temp_dominated_data_source = ColumnDataSource(data=self.observations_df[~self.observations_df['is_pareto']])

        self.data_source.data = dict(temp_data_source.data)
        self.pareto_data_source.data = dict(temp_pareto_data_source.data)
        self.dominated_data_source.data = dict(temp_dominated_data_source.data)

    def _construct_observations(self):
        features_df = self.optimization_problem.construct_feature_dataframe(parameters_df=self.parameters_df, context_df=self.context_df, product=False)
        projected_features_df = self._feature_space_adapter.project_dataframe(features_df)
        observations_df = pd.concat([projected_features_df, self.objectives_df], axis=1)
        observations_df['is_pareto'] = False
        observations_df.loc[self.pareto_df.index, 'is_pareto'] = True
        return observations_df

#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import pandas as pd

from mlos.Logger import create_logger
from mlos.Optimizers.OptimizationProblem import Objective, SeriesObjective
from mlos.Optimizers.RegressionModels.HomogeneousRandomForestConfigStore import homogeneous_random_forest_config_store
from mlos.Optimizers.RegressionModels.HomogeneousRandomForestRegressionModel import HomogeneousRandomForestRegressionModel
from mlos.Optimizers.RegressionModels.NaiveMultiObjectiveRegressionModel import NaiveMultiObjectiveRegressionModel
from mlos.Optimizers.RegressionModels.RegressionModel import RegressionModel
from mlos.Optimizers.RegressionModels.GoodnessOfFitMetrics import DataSetType
from mlos.Optimizers.RegressionModels.MultiObjectiveGoodnessOfFitMetrics import MultiObjectiveGoodnessOfFitMetrics
from mlos.Optimizers.RegressionModels.MultiObjectivePrediction import MultiObjectivePrediction
from mlos.Optimizers.RegressionModels.MultiObjectiveRegressionModel import MultiObjectiveRegressionModel
from mlos.Optimizers.RegressionModels.MultiObjectiveRegressionModelFitState import MultiObjectiveRegressionModelFitState
from mlos.Optimizers.RegressionModels.SeriesHomogeneousRandomForestRegressionModel import \
    SeriesHomogeneousRandomForestRegressionModel
from mlos.Spaces import Hypergrid, Point, SimpleHypergrid
from mlos.Utils.KeyOrderedDict import KeyOrderedDict


class SeriesAwareMultiObjectiveHomogeneousRandomForest(NaiveMultiObjectiveRegressionModel):
    """TODO ZACK: do comment. /\\ - This is a comically long name.

    """
    def __init__(
            self,
            model_config: Point,
            input_space: Hypergrid,
            output_space: Hypergrid,
            objectives: list[Objective],
            logger=None
    ):
        NaiveMultiObjectiveRegressionModel.__init__(
            self,
            model_type=HomogeneousRandomForestRegressionModel,
            model_config=model_config,
            input_space=input_space,
            output_space=output_space,
            logger=logger
        )

        print("ZACK CREATING SERIES AWARE MULTI OBJECTIVE BLAH")
        # TODO ZACK: Adam, is there python syntax sugar to build this dict?
        self._name_to_objective_dict = {}
        for objective in objectives:
            self._name_to_objective_dict[objective.name] = objective

        # We just need to assert that the model config belongs in homogeneous_random_forest_config_store.parameter_space.
        # A more elaborate solution might be needed down the road, but for now this simple solution should suffice.
        #
        assert model_config in homogeneous_random_forest_config_store.parameter_space

        for output_dimension in output_space.dimensions:
            assert output_dimension.name in self._name_to_objective_dict, "Output dimension not listed in objectives"
            output_objective = self._name_to_objective_dict[output_dimension.name]
            if isinstance(output_objective, SeriesObjective):
                random_forest = SeriesHomogeneousRandomForestRegressionModel(
                    model_config=model_config,
                    input_space=input_space,
                    objective=output_objective,
                    # series-objective rather than series_objective is used in this case to prevent future naming confusion if
                    # output_dimension.name = xxx_series. However this should be entirely internal so it wont matter...
                    #
                    output_space=SimpleHypergrid(name=f"{output_dimension.name}_series-objective", dimensions=[output_dimension]),
                    logger=self.logger
                )
            else:
                random_forest = HomogeneousRandomForestRegressionModel(
                    model_config=model_config,
                    input_space=input_space,
                    output_space=SimpleHypergrid(name=f"{output_dimension.name}_objective", dimensions=[output_dimension]),
                    logger=self.logger
                )
            self._regressors_by_objective_name[output_dimension.name] = random_forest

    def fit(
            self,
            features_df: pd.DataFrame,
            targets_df: pd.DataFrame,
            iteration_number: int
    ) -> None:
        for objective_name, regressor in self._regressors_by_objective_name:
            regressor.fit(
                feature_values_pandas_frame=features_df,
                target_values_pandas_frame=targets_df[[regressor.output_space.dimensions[0].name]],
                iteration_number=iteration_number
            )

    def predict(
            self,
            features_df: pd.DataFrame,
            include_only_valid_rows: bool = True
    ) -> MultiObjectivePrediction:
        multi_objective_predicitons = MultiObjectivePrediction(objective_names=self.output_dimension_names)
        for objective_name, regressor in self._regressors_by_objective_name:
            prediction = regressor.predict(feature_values_pandas_frame=features_df, include_only_valid_rows=include_only_valid_rows)
            multi_objective_predicitons[objective_name] = prediction
        return multi_objective_predicitons

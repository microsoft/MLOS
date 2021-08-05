#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import pandas as pd

from mlos.Logger import create_logger
from mlos.Optimizers.RegressionModels.GoodnessOfFitMetrics import DataSetType
from mlos.Optimizers.RegressionModels.HomogeneousRandomForestRegressionModel import HomogeneousRandomForestRegressionModel
from mlos.Optimizers.RegressionModels.HomogeneousRandomForestConfigStore import homogeneous_random_forest_config_store
from mlos.Optimizers.RegressionModels.MultiObjectiveGoodnessOfFitMetrics import MultiObjectiveGoodnessOfFitMetrics
from mlos.Optimizers.RegressionModels.MultiObjectivePrediction import MultiObjectivePrediction
from mlos.Optimizers.RegressionModels.MultiObjectiveRegressionModel import MultiObjectiveRegressionModel
from mlos.Optimizers.RegressionModels.MultiObjectiveRegressionModelFitState import MultiObjectiveRegressionModelFitState
from mlos.Spaces import Hypergrid, Point, SimpleHypergrid
from mlos.Utils.KeyOrderedDict import KeyOrderedDict


class MultiObjectiveHomogeneousRandomForest(MultiObjectiveRegressionModel):
    """Maintains multiple HomogeneousRandomForestRegressionModels each predicting a different objective.

    All single-objective models are configured according to model_config.

    """
    def __init__(
            self,
            model_config: Point,
            input_space: Hypergrid,
            output_space: Hypergrid,
            logger=None
    ):
        MultiObjectiveRegressionModel.__init__(
            self,
            model_type=type(self),
            model_config=model_config,
            input_space=input_space,
            output_space=output_space
        )
        if logger is None:
            logger = create_logger("MultiObjectiveHomogeneousRandomForest")
        self.logger = logger

        # We just need to assert that the model config belongs in homogeneous_random_forest_config_store.parameter_space.
        # A more elaborate solution might be needed down the road, but for now this simple solution should suffice.
        #
        assert model_config in homogeneous_random_forest_config_store.parameter_space

        self._regressors_by_objective_name = KeyOrderedDict(ordered_keys=self.output_dimension_names, value_type=HomogeneousRandomForestRegressionModel)

        for output_dimension in output_space.dimensions:
            random_forest = HomogeneousRandomForestRegressionModel(
                model_config=model_config,
                input_space=input_space,
                output_space=SimpleHypergrid(name=f"{output_dimension.name}_objective", dimensions=[output_dimension]),
                logger=self.logger
            )
            self._regressors_by_objective_name[output_dimension.name] = random_forest

    @property
    def fit_state(self) -> MultiObjectiveRegressionModelFitState:
        multi_objective_fit_state = MultiObjectiveRegressionModelFitState(objective_names=self.output_dimension_names)
        for objective_name, random_forest in self._regressors_by_objective_name:
            multi_objective_fit_state[objective_name] = random_forest.fit_state

        return multi_objective_fit_state

    @property
    def trained(self) -> bool:
        return all(random_forest.trained for _, random_forest in self._regressors_by_objective_name)

    def fit(self, features_df: pd.DataFrame, targets_df: pd.DataFrame, iteration_number: int) -> None:
        for objective_name, random_forest in self._regressors_by_objective_name:
            if objective_name not in targets_df.columns:
                continue

            random_forest.fit(
                feature_values_pandas_frame=features_df,
                target_values_pandas_frame=targets_df[[objective_name]],
                iteration_number=iteration_number
            )

    def predict(self, features_df: pd.DataFrame, include_only_valid_rows: bool = True) -> MultiObjectivePrediction:
        multi_objective_predicitons = MultiObjectivePrediction(objective_names=self.output_dimension_names)
        for objective_name, random_forest in self._regressors_by_objective_name:
            prediction = random_forest.predict(feature_values_pandas_frame=features_df, include_only_valid_rows=include_only_valid_rows)
            multi_objective_predicitons[objective_name] = prediction
        return multi_objective_predicitons

    def compute_goodness_of_fit(self, features_df: pd.DataFrame, targets_df: pd.DataFrame, data_set_type: DataSetType) -> MultiObjectiveGoodnessOfFitMetrics:
        multi_objective_goodness_of_fit_metrics = MultiObjectiveGoodnessOfFitMetrics(objective_names=self.output_dimension_names)
        for objective_name, random_forest in self._regressors_by_objective_name:
            gof_metrics = random_forest.compute_goodness_of_fit(features_df=features_df, target_df=targets_df[[objective_name]], data_set_type=data_set_type)
            multi_objective_goodness_of_fit_metrics[objective_name] = gof_metrics
        return multi_objective_goodness_of_fit_metrics

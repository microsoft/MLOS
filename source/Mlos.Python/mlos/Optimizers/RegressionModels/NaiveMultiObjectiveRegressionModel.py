#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import pandas as pd

from mlos.Logger import create_logger
from mlos.Optimizers.RegressionModels.RegressionModel import RegressionModel
from mlos.Optimizers.RegressionModels.GoodnessOfFitMetrics import DataSetType
from mlos.Optimizers.RegressionModels.MultiObjectiveGoodnessOfFitMetrics import MultiObjectiveGoodnessOfFitMetrics
from mlos.Optimizers.RegressionModels.MultiObjectivePrediction import MultiObjectivePrediction
from mlos.Optimizers.RegressionModels.MultiObjectiveRegressionModel import MultiObjectiveRegressionModel
from mlos.Optimizers.RegressionModels.MultiObjectiveRegressionModelFitState import MultiObjectiveRegressionModelFitState
from mlos.Spaces import Hypergrid, Point
from mlos.Utils.KeyOrderedDict import KeyOrderedDict

class NaiveMultiObjectiveRegressionModel(MultiObjectiveRegressionModel):
    """A base class for naive multi-objective regression models.

    Works by simply combining multiple single objective models.
    """
    def __init__(
            self,
            model_type: type,
            model_config: Point,
            input_space: Hypergrid,
            output_space: Hypergrid,
            logger=None
    ):
        assert issubclass(model_type, RegressionModel)
        MultiObjectiveRegressionModel.__init__(
            self,
            model_type=model_type,
            model_config=model_config,
            input_space=input_space,
            output_space=output_space
        )
        if logger is None:
            logger = create_logger("MultiObjectiveHomogeneousRandomForest")
        self.logger = logger

        self._regressors_by_objective_name = KeyOrderedDict(ordered_keys=self.output_dimension_names, value_type=model_type)

    @property
    def fit_state(self) -> MultiObjectiveRegressionModelFitState:
        multi_objective_fit_state = MultiObjectiveRegressionModelFitState(objective_names=self.output_dimension_names)
        for objective_name, regressor in self._regressors_by_objective_name:
            multi_objective_fit_state[objective_name] = regressor.fit_state

        return multi_objective_fit_state

    @property
    def trained(self) -> bool:
        return all(regressor.trained for _, regressor in self._regressors_by_objective_name)

    def fit(
            self,
            features_df: pd.DataFrame,
            targets_df: pd.DataFrame,
            iteration_number: int
    ) -> None:
        for objective_name, regressor in self._regressors_by_objective_name:
            if objective_name not in targets_df.columns:
                continue

            regressor.fit(
                feature_values_pandas_frame=features_df,
                target_values_pandas_frame=targets_df[[objective_name]],
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

    def compute_goodness_of_fit(
            self,
            features_df: pd.DataFrame,
            targets_df: pd.DataFrame,
            data_set_type: DataSetType
    ) -> MultiObjectiveGoodnessOfFitMetrics:
        multi_objective_goodness_of_fit_metrics = MultiObjectiveGoodnessOfFitMetrics(objective_names=self.output_dimension_names)
        for objective_name, regressor in self._regressors_by_objective_name:
            gof_metrics = regressor.compute_goodness_of_fit(features_df=features_df, target_df=targets_df[[objective_name]], data_set_type=data_set_type)
            multi_objective_goodness_of_fit_metrics[objective_name] = gof_metrics
        return multi_objective_goodness_of_fit_metrics

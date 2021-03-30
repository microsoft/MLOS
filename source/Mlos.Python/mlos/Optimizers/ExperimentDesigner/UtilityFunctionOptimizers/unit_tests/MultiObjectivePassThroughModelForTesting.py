#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import numpy as np
import pandas as pd

from mlos.Logger import create_logger
from mlos.OptimizerEvaluationTools.ObjectiveFunctionFactory import ObjectiveFunctionFactory, objective_function_config_store
from mlos.Optimizers.RegressionModels.GoodnessOfFitMetrics import DataSetType
from mlos.Optimizers.RegressionModels.MultiObjectiveGoodnessOfFitMetrics import MultiObjectiveGoodnessOfFitMetrics
from mlos.Optimizers.RegressionModels.MultiObjectivePrediction import MultiObjectivePrediction
from mlos.Optimizers.RegressionModels.MultiObjectiveRegressionModel import MultiObjectiveRegressionModel
from mlos.Optimizers.RegressionModels.MultiObjectiveRegressionModelFitState import MultiObjectiveRegressionModelFitState
from mlos.Optimizers.RegressionModels.Prediction import Prediction
from mlos.Spaces import CategoricalDimension, ContinuousDimension, DiscreteDimension, Hypergrid, Point, SimpleHypergrid
from mlos.Spaces.Configs.ComponentConfigStore import ComponentConfigStore


multi_objective_pass_through_model_config_store = ComponentConfigStore(
    parameter_space=SimpleHypergrid(
        name="multi_objective_pass_through_model_config",
        dimensions=[
            CategoricalDimension(name="uncertainty_type", values=["constant", "coefficient_of_variation"]),
            CategoricalDimension(name="use_objective_function", values=[True]),
            DiscreteDimension(name="predicted_value_degrees_of_freedom", min=3, max=10000)
        ]
    ).join(
        on_external_dimension=CategoricalDimension(name="uncertainty_type", values=["constant"]),
        subgrid=SimpleHypergrid(
            name="constant_uncertainty_config",
            dimensions=[ContinuousDimension(name="value", min=0, max=2 ** 10)]
        )
    ).join(
        on_external_dimension=CategoricalDimension(name="uncertainty_type", values=["coefficient_of_variation"]),
        subgrid=SimpleHypergrid(
            name="coefficient_of_variation_config",
            dimensions=[ContinuousDimension(name="value", min=0, max=1)]
        )
    ).join(
        on_external_dimension=CategoricalDimension(name="use_objective_function", values=[True]),
        subgrid=objective_function_config_store.parameter_space
    ),
    default=Point(
        uncertainty_type="constant",
        use_objective_function=True,
        predicted_value_degrees_of_freedom=10,
        constant_uncertainty_config=Point(value=1),
        objective_function_config=objective_function_config_store.get_config_by_name("three_level_quadratic")
    ),
    description=""
)

multi_objective_pass_through_model_config_store.add_config_by_name(
    config_name="three_level_quadratic",
    config_point=Point(
        uncertainty_type="constant",
        use_objective_function=True,
        predicted_value_degrees_of_freedom=10,
        constant_uncertainty_config=Point(value=1),
        objective_function_config=objective_function_config_store.get_config_by_name("three_level_quadratic")
    )
)

multi_objective_pass_through_model_config_store.add_config_by_name(
    config_name="multi_objective_waves_3_params_2_objectives_half_pi_phase_difference",
    config_point=Point(
        uncertainty_type="coefficient_of_variation",
        use_objective_function=True,
        predicted_value_degrees_of_freedom=10,
        coefficient_of_variation_config=Point(value=0.1),
        objective_function_config=objective_function_config_store.get_config_by_name("multi_objective_waves_3_params_2_objectives_half_pi_phase_difference")
    )
)


class MultiObjectivePassThroughModelForTesting(MultiObjectiveRegressionModel):
    """Used for testing. Exposes the MultiObjectiveRegressionModel interface, but is in fact not a model.

        This dummy wraps around any of the synthetic functions and when it's time to make a prediction it simply evaluates that function,
    adds some preconfigured uncertainty of its own and returns. For now register() is a noop, but we could conceivably make the observations
    reduce uncertainty in their vicinity to achieve more dynamic behavior in the future.

    """

    _PREDICTOR_OUTPUT_COLUMNS = [
        Prediction.LegalColumnNames.IS_VALID_INPUT,
        Prediction.LegalColumnNames.PREDICTED_VALUE,
        Prediction.LegalColumnNames.PREDICTED_VALUE_VARIANCE,
        Prediction.LegalColumnNames.PREDICTED_VALUE_DEGREES_OF_FREEDOM
    ]

    def __init__(
            self,
            model_config: Point,
            input_space: Hypergrid = None,
            output_space: Hypergrid = None,
            logger=None
    ):
        assert model_config in multi_objective_pass_through_model_config_store.parameter_space
        self.objective_function = ObjectiveFunctionFactory.create_objective_function(objective_function_config=model_config.objective_function_config)


        MultiObjectiveRegressionModel.__init__(
            self,
            model_type=type(self),
            model_config=model_config,
            input_space=self.objective_function.default_optimization_problem.feature_space,
            output_space=self.objective_function.output_space
        )

        if logger is None:
            logger = create_logger(self.__class__.__name__)
        self.logger = logger


    @property
    def fit_state(self) -> MultiObjectiveRegressionModelFitState:
        raise NotImplementedError

    @property
    def trained(self) -> bool:
        return True

    def fit(self, features_df: pd.DataFrame, targets_df: pd.DataFrame, iteration_number: int) -> None:
        ...

    def predict(self, features_df: pd.DataFrame, include_only_valid_rows: bool = True) -> MultiObjectivePrediction:
        parameters_df, context_df = self.objective_function.default_optimization_problem.deconstruct_feature_dataframe(features_df=features_df)
        target_values_df = self.objective_function.evaluate_dataframe(dataframe=parameters_df)
        multi_objective_predicitons = MultiObjectivePrediction(objective_names=self.output_space.dimension_names)
        for objective_name in multi_objective_predicitons.ordered_keys:
            prediction = Prediction(objective_name=objective_name, predictor_outputs=self._PREDICTOR_OUTPUT_COLUMNS, allow_extra_columns=True)
            prediction_df = pd.DataFrame()
            prediction_df[Prediction.LegalColumnNames.IS_VALID_INPUT.value] = True
            prediction_df[Prediction.LegalColumnNames.PREDICTED_VALUE.value] = target_values_df[objective_name]
            if self.model_config.uncertainty_type == "coefficient_of_variation":
                prediction_df[Prediction.LegalColumnNames.PREDICTED_VALUE_VARIANCE.value] = np.abs(target_values_df[objective_name] * self.model_config.coefficient_of_variation_config.value)
            elif self.model_config.uncertainty_type == "constant":
                prediction_df[Prediction.LegalColumnNames.PREDICTED_VALUE_VARIANCE.value] = self.model_config.constant_uncertainty_config.value
            else:
                raise RuntimeError(f"Unrecognized uncertainty type: {self.model_config.uncertainty_type}")

            prediction_df[Prediction.LegalColumnNames.PREDICTED_VALUE_DEGREES_OF_FREEDOM.value] = self.model_config.predicted_value_degrees_of_freedom
            prediction.set_dataframe(dataframe=prediction_df)
            multi_objective_predicitons[objective_name] = prediction

        return multi_objective_predicitons

    def compute_goodness_of_fit(self, features_df: pd.DataFrame, targets_df: pd.DataFrame, data_set_type: DataSetType) -> MultiObjectiveGoodnessOfFitMetrics:
        raise NotImplementedError

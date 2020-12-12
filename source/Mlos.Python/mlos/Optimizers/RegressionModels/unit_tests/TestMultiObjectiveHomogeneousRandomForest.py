#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import pytest

import mlos.global_values
from mlos.OptimizerEvaluationTools.ObjectiveFunctionFactory import ObjectiveFunctionFactory, objective_function_config_store
from mlos.Optimizers.RegressionModels.GoodnessOfFitMetrics import DataSetType
from mlos.Optimizers.RegressionModels.HomogeneousRandomForestConfigStore import homogeneous_random_forest_config_store
from mlos.Optimizers.RegressionModels.MultiObjectiveHomogeneousRandomForest import MultiObjectiveHomogeneousRandomForest
from mlos.Logger import create_logger

class TestMultiObjectiveHomogeneousRandomForest:

    @classmethod
    def setup_class(cls) -> None:
        mlos.global_values.declare_singletons()
        cls.logger = create_logger("TestMultiObjectiveHomogeneousRandomForest")

    @pytest.mark.parametrize('objective_function_config_name', ["2d_hypersphere_minimize_some", "10d_hypersphere_minimize_some"])
    def test_default_config(self, objective_function_config_name):
        objective_function_config = objective_function_config_store.get_config_by_name(objective_function_config_name)
        objective_function = ObjectiveFunctionFactory.create_objective_function(objective_function_config)

        rf_config = homogeneous_random_forest_config_store.default
        multi_objective_rf = MultiObjectiveHomogeneousRandomForest(
            model_config=rf_config,
            input_space=objective_function.parameter_space,
            output_space=objective_function.output_space,
            logger=self.logger
        )

        num_training_samples = 10000
        num_testing_samples = 1000
        train_params_df = objective_function.parameter_space.random_dataframe(num_samples=num_training_samples)
        train_objectives_df = objective_function.evaluate_dataframe(train_params_df)

        test_params_df = objective_function.parameter_space.random_dataframe(num_samples=num_testing_samples)
        test_objectives_df = objective_function.evaluate_dataframe(test_params_df)

        multi_objective_rf.fit(features_df=train_params_df, targets_df=train_objectives_df, iteration_number=num_training_samples)
        multi_objective_predictions = multi_objective_rf.predict(features_df=train_params_df, include_only_valid_rows=True)

        for objective_name in objective_function.output_space.dimension_names:
            objective_predictions = multi_objective_predictions[objective_name]
            assert len(objective_predictions.get_dataframe().index) == num_training_samples


        # TRAINING DATA
        #
        print("------------------------------------------------------------------------------------")
        print("--------------------------------------- TRAIN --------------------------------------")
        print("------------------------------------------------------------------------------------")
        training_gof = multi_objective_rf.compute_goodness_of_fit(features_df=train_params_df, targets_df=train_objectives_df, data_set_type=DataSetType.TRAIN)
        for objective_name in objective_function.output_space.dimension_names:
            print("------------------------------------------------------------------------------------")
            print(objective_name)
            print(training_gof[objective_name].to_json(indent=2))

        # TESTING DATA
        print("------------------------------------------------------------------------------------")
        print("--------------------------------------- TEST ---------------------------------------")
        print("------------------------------------------------------------------------------------")
        testing_gof = multi_objective_rf.compute_goodness_of_fit(features_df=test_params_df, targets_df=test_objectives_df, data_set_type=DataSetType.TEST_KNOWN_RANDOM)
        for objective_name in objective_function.output_space.dimension_names:
            print("------------------------------------------------------------------------------------")
            print(objective_name)
            print(testing_gof[objective_name].to_json(indent=2))






#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import pytest

import mlos.global_values
from mlos.OptimizerEvaluationTools.ObjectiveFunctionFactory import ObjectiveFunctionFactory, objective_function_config_store
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

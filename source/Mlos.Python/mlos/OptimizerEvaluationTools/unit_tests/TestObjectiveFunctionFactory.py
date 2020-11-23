#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import pytest
import warnings

from mlos.OptimizerEvaluationTools.ObjectiveFunctionFactory import ObjectiveFunctionFactory, objective_function_config_store
import mlos.global_values



class TestObjectiveFunctionFactory:

    @classmethod
    def classSetUp(cls):
        mlos.global_values.declare_singletons()
        warnings.simplefilter("error", category=FutureWarning)

    @pytest.mark.parametrize("config_name", [config.name for config in objective_function_config_store.list_named_configs()])
    def test_named_configs(self, config_name):
        objective_function_config = objective_function_config_store.get_config_by_name(config_name)
        print(objective_function_config.to_json(indent=2))
        objective_function = ObjectiveFunctionFactory.create_objective_function(objective_function_config=objective_function_config)

        for _ in range(100):
            random_point = objective_function.parameter_space.random()
            value = objective_function.evaluate_point(random_point)
            assert value in objective_function.output_space

        for i in range(1, 100):
            random_dataframe = objective_function.parameter_space.random_dataframe(num_samples=i)
            values_df = objective_function.evaluate_dataframe(random_dataframe)
            assert values_df.index.equals(random_dataframe.index)

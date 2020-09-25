#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import unittest
import warnings

from mlos.OptimizerEvaluationTools.ObjectiveFunctionFactory import ObjectiveFunctionFactory, objective_function_config_store
import mlos.global_values



class TestObjectiveFunctionFactory(unittest.TestCase):

    @classmethod
    def classSetUp(cls):
        mlos.global_values.declare_singletons()
        warnings.simplefilter("error", category=FutureWarning)

    def setUp(self):
        ...

    def test_default(self):

        named_configs = objective_function_config_store.list_named_configs()

        objective_function_configs_to_test = [
            named_config.config_point for named_config in named_configs
        ]

        for objective_function_config in objective_function_configs_to_test:
            print(objective_function_config.to_json(indent=2))
            objective_function = ObjectiveFunctionFactory.create_objective_function(objective_function_config=objective_function_config)
            default_polynomials_domain = objective_function.parameter_space
            for _ in range(100):
                random_point = default_polynomials_domain.random()
                value = objective_function.evaluate_point(random_point)
                self.assertTrue(value in objective_function.output_space)

            for i in range(1, 100):
                random_dataframe = default_polynomials_domain.random_dataframe(num_samples=i)
                values_df = objective_function.evaluate_dataframe(random_dataframe)
                self.assertTrue(values_df.index.equals(random_dataframe.index))

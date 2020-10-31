#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import concurrent.futures
import os
import pickle
import unittest

import pandas as pd

import mlos.global_values
from mlos.OptimizerEvaluationTools.OptimizerEvaluator import OptimizerEvaluator
from mlos.OptimizerEvaluationTools.OptimizerEvaluatorConfigStore import optimizer_evaluator_config_store
from mlos.OptimizerEvaluationTools.ObjectiveFunctionFactory import objective_function_config_store
from mlos.Optimizers.BayesianOptimizerFactory import bayesian_optimizer_config_store
from mlos.Optimizers.RegressionModels.GoodnessOfFitMetrics import DataSetType
from mlos.Tracer import Tracer, traced



class TestOptimizerEvaluator(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        mlos.global_values.declare_singletons()
        mlos.global_values.tracer = Tracer(actor_id=cls.__name__, thread_id=0)

        cls.temp_dir = os.path.join(os.getcwd(), "temp")
        if not os.path.exists(cls.temp_dir):
            os.mkdir(cls.temp_dir)

    @classmethod
    def tearDownClass(cls) -> None:
        trace_output_path = os.path.join(cls.temp_dir, "TestOptimizerEvaluator.json")
        print(f"Dumping trace to {trace_output_path}")
        mlos.global_values.tracer.dump_trace_to_file(output_file_path=trace_output_path)

    def test_defaults(self):
        """Tests default optimizer configurations against default objective functions."""
        optimizer_evaluator_config = optimizer_evaluator_config_store.default

        # We want to test this functionality so let's make sure that nobody accidentally disables it in the default config.
        #
        self.assertTrue(optimizer_evaluator_config.include_pickled_optimizer_in_report)
        self.assertTrue(optimizer_evaluator_config.include_pickled_objective_function_in_report)
        self.assertTrue(optimizer_evaluator_config.report_regression_model_goodness_of_fit)
        self.assertTrue(optimizer_evaluator_config.report_optima_over_time)
        self.assertTrue(optimizer_evaluator_config.include_execution_trace_in_report)

        optimizer_config = bayesian_optimizer_config_store.default
        objective_function_config = objective_function_config_store.default

        print(optimizer_evaluator_config.to_json(indent=2))
        print(optimizer_config.to_json(indent=2))
        print(objective_function_config.to_json(indent=2))

        optimizer_evaluator = OptimizerEvaluator(
            optimizer_evaluator_config=optimizer_evaluator_config,
            objective_function_config=objective_function_config,
            optimizer_config=optimizer_config
        )

        optimizer_evaluation_report = optimizer_evaluator.evaluate_optimizer()

        with pd.option_context('display.max_columns', 100):
            print(optimizer_evaluation_report.regression_model_goodness_of_fit_state.get_goodness_of_fit_dataframe(DataSetType.TRAIN).tail())
            for optimum_name, optimum_over_time in optimizer_evaluation_report.optima_over_time.items():
                print("#####################################################################################################")
                print(optimum_name)
                print(optimum_over_time.get_dataframe().tail(10))
                print("#####################################################################################################")

        optimizer_evaluation_report.write_to_disk(target_folder=self.temp_dir)

        # Now let's do it again with the unpickled optimizer.
        #
        unpickled_objective_function = pickle.loads(optimizer_evaluation_report.pickled_objective_function_initial_state)
        unpickled_optimizer = pickle.loads(optimizer_evaluation_report.pickled_optimizer_initial_state)
        optimizer_evaluator_2 = OptimizerEvaluator(
            optimizer_evaluator_config=optimizer_evaluator_config,
            objective_function=unpickled_objective_function,
            optimizer=unpickled_optimizer
        )

        optimizer_evaluation_report_2 = optimizer_evaluator_2.evaluate_optimizer()
        with pd.option_context('display.max_columns', 100):
            print(optimizer_evaluation_report_2.regression_model_goodness_of_fit_state.get_goodness_of_fit_dataframe(DataSetType.TRAIN).tail())
            for optimum_name, optimum_over_time in optimizer_evaluation_report_2.optima_over_time.items():
                print("#####################################################################################################")
                print(optimum_name)
                print(optimum_over_time.get_dataframe().tail(10))
                print("#####################################################################################################")


    def test_named_configs(self):
        """Tests all named optimizer configurations against all named objective functions."""
        optimizer_named_configs = bayesian_optimizer_config_store.list_named_configs()
        num_optimizer_configs = len(optimizer_named_configs)
        objective_function_named_configs = objective_function_config_store.list_named_configs()
        num_objective_function_configs = len(objective_function_named_configs)

        num_tests = 7

        with traced(scope_name="parallel_tests"), concurrent.futures.ProcessPoolExecutor(max_workers=4) as executor:
            outstanding_futures = set()

            for i in range(num_tests):
                named_optimizer_config = optimizer_named_configs[i % num_optimizer_configs]
                named_objective_function_config = objective_function_named_configs[i % num_objective_function_configs]

                print("#####################################################################################################")
                print(named_optimizer_config)
                print(named_objective_function_config)

                optimizer_evaluator_config = optimizer_evaluator_config_store.get_config_by_name(name="parallel_unit_tests_config")
                optimizer_config = named_optimizer_config.config_point
                objective_function_config = named_objective_function_config.config_point

                optimizer_evaluator = OptimizerEvaluator(
                    optimizer_evaluator_config=optimizer_evaluator_config,
                    objective_function_config=objective_function_config,
                    optimizer_config=optimizer_config
                )

                future = executor.submit(optimizer_evaluator.evaluate_optimizer)
                outstanding_futures.add(future)

            done_futures, outstanding_futures = concurrent.futures.wait(outstanding_futures, return_when=concurrent.futures.ALL_COMPLETED)

            for future in done_futures:
                optimizer_evaluation_report = future.result()
                mlos.global_values.tracer.trace_events.extend(optimizer_evaluation_report.execution_trace)

                with pd.option_context('display.max_columns', 100):
                    print(optimizer_evaluation_report.regression_model_goodness_of_fit_state.get_goodness_of_fit_dataframe(DataSetType.TRAIN).tail())
                    for optimum_name, optimum_over_time in optimizer_evaluation_report.optima_over_time.items():
                        print("#####################################################################################################")
                        print(optimum_name)
                        print(optimum_over_time.get_dataframe().tail(10))
                        print("#####################################################################################################")

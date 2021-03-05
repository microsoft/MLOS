#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import json
import math
import os
import pickle

import pandas as pd
import pytest

import mlos.global_values
from mlos.Logger import create_logger
from mlos.OptimizerEvaluationTools.OptimizerEvaluator import OptimizerEvaluator
from mlos.OptimizerEvaluationTools.OptimizerEvaluatorConfigStore import optimizer_evaluator_config_store
from mlos.OptimizerEvaluationTools.OptimizerEvaluationReport import OptimizerEvaluationReport
from mlos.OptimizerEvaluationTools.ObjectiveFunctionFactory import objective_function_config_store
from mlos.Optimizers.BayesianOptimizerFactory import bayesian_optimizer_config_store
from mlos.Optimizers.RegressionModels.GoodnessOfFitMetrics import DataSetType, GoodnessOfFitMetrics
from mlos.Spaces import Point
from mlos.Tracer import Tracer, traced



class TestOptimizerEvaluator:

    @classmethod
    def setup_class(cls) -> None:
        mlos.global_values.declare_singletons()
        mlos.global_values.tracer = Tracer(actor_id=cls.__name__, thread_id=0)

        cls.temp_dir = os.path.join(os.getcwd(), "temp")
        if not os.path.exists(cls.temp_dir):
            os.mkdir(cls.temp_dir)

        cls.logger = create_logger("TestOptimizerEvaluator")

    @classmethod
    def teardown_class(cls) -> None:
        trace_output_path = os.path.join(cls.temp_dir, "TestOptimizerEvaluator.json")
        print(f"Dumping trace to {trace_output_path}")
        mlos.global_values.tracer.dump_trace_to_file(output_file_path=trace_output_path)

    def test_defaults(self):
        """Tests default optimizer configurations against default objective functions."""
        optimizer_evaluator_config = optimizer_evaluator_config_store.default
        optimizer_evaluator_config.num_iterations = 100

        # We want to test this functionality so let's make sure that nobody accidentally disables it in the default config.
        #
        assert optimizer_evaluator_config.include_pickled_optimizer_in_report
        assert optimizer_evaluator_config.include_pickled_objective_function_in_report
        assert optimizer_evaluator_config.report_regression_model_goodness_of_fit
        assert optimizer_evaluator_config.report_optima_over_time
        assert optimizer_evaluator_config.include_execution_trace_in_report

        optimizer_config = bayesian_optimizer_config_store.default
        objective_function_config = objective_function_config_store.default

        self.logger.info(optimizer_evaluator_config.to_json(indent=2))
        self.logger.info(optimizer_config.to_json(indent=2))
        self.logger.info(objective_function_config.to_json(indent=2))

        optimizer_evaluator = OptimizerEvaluator(
            optimizer_evaluator_config=optimizer_evaluator_config,
            objective_function_config=objective_function_config,
            optimizer_config=optimizer_config
        )

        optimizer_evaluation_report = optimizer_evaluator.evaluate_optimizer()
        assert optimizer_evaluation_report.success

        for objective_name, regression_model_fit_state in optimizer_evaluation_report.regression_model_fit_state:
            with pd.option_context('display.max_columns', 100):
                self.logger.info(regression_model_fit_state.get_goodness_of_fit_dataframe(DataSetType.TRAIN).tail())
                for optimum_name, optimum_over_time in optimizer_evaluation_report.optima_over_time.items():
                    self.logger.info("#####################################################################################################")
                    self.logger.info(optimum_name)
                    self.logger.info(optimum_over_time.get_dataframe().tail(10))
                    self.logger.info("#####################################################################################################")

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
        for objective_name, single_objective_regression_model_fit_state in optimizer_evaluation_report_2.regression_model_fit_state:
            with pd.option_context('display.max_columns', 100):
                self.logger.info(single_objective_regression_model_fit_state.get_goodness_of_fit_dataframe(DataSetType.TRAIN).tail())
                for optimum_name, optimum_over_time in optimizer_evaluation_report_2.optima_over_time.items():
                    self.logger.info("#####################################################################################################")
                    self.logger.info(optimum_name)
                    self.logger.info(optimum_over_time.get_dataframe().tail(10))
                    self.logger.info("#####################################################################################################")



        optimizer_evaluation_report.write_to_disk(target_folder=self.temp_dir)
        restored_evaluation_report = OptimizerEvaluationReport.read_from_disk(target_folder=self.temp_dir)

        assert optimizer_evaluation_report.success == restored_evaluation_report.success
        assert optimizer_evaluation_report.num_optimization_iterations == restored_evaluation_report.num_optimization_iterations
        assert optimizer_evaluation_report.evaluation_frequency == restored_evaluation_report.evaluation_frequency
        assert optimizer_evaluation_report.exception == restored_evaluation_report.exception
        assert optimizer_evaluation_report.exception_traceback == restored_evaluation_report.exception_traceback

        with open(os.path.join(self.temp_dir, "execution_trace.json")) as in_file:
            trace = json.load(in_file)
        assert len(trace) > 100
        assert all(key in trace[0] for key in ["ts", "name", "ph", "cat", "pid", "tid", "args"])

        for objective_name, fit_state in restored_evaluation_report.regression_model_fit_state:
            gof_df = fit_state.get_goodness_of_fit_dataframe()
            assert len(gof_df.index) > 0
            assert all((col_name in gof_df.columns.values or col_name == "data_set_type") for col_name in GoodnessOfFitMetrics._fields)
            assert all(gof_df[col_name].is_monotonic for col_name in ["last_refit_iteration_number", "observation_count", "prediction_count"])

        for key, optimum_over_time in restored_evaluation_report.optima_over_time.items():
            assert optimizer_evaluation_report.optima_over_time[key].get_dataframe().equals(optimum_over_time.get_dataframe())


        assert restored_evaluation_report.optimizer_configuration == optimizer_config
        assert restored_evaluation_report.objective_function_configuration == objective_function_config

        unpickled_objective_function = pickle.loads(restored_evaluation_report.pickled_objective_function_initial_state)
        assert unpickled_objective_function.objective_function_config == objective_function_config.polynomial_objective_config

        for _ in range(10):
            random_pt = unpickled_objective_function.parameter_space.random()
            assert unpickled_objective_function.evaluate_point(random_pt) in unpickled_objective_function.output_space

        # Lastly let's double check the pickled optimizers
        #
        assert len(restored_evaluation_report.pickled_optimizers_over_time) == 11

        # Finally, let's make sure that the optimizers serialized to disk are usable.
        #
        final_optimizer_from_disk = pickle.loads(restored_evaluation_report.pickled_optimizers_over_time[99])
        final_optimizer_from_report = pickle.loads(optimizer_evaluation_report.pickled_optimizers_over_time[99])

        for _ in range(100):
            assert final_optimizer_from_disk.suggest() in final_optimizer_from_report.optimization_problem.parameter_space


    @pytest.mark.parametrize('test_num', [i for i in range(10)])
    def test_named_configs(self, test_num):
        """Tests named optimizer configurations against named objective functions.

        It is prohibitively expensive to test the entire cross product so we test only its subset, but in such a way that
        each configuration will be tested at least once.
        """
        optimizer_named_configs = bayesian_optimizer_config_store.list_named_configs()
        num_optimizer_configs = len(optimizer_named_configs)
        objective_function_named_configs = objective_function_config_store.list_named_configs()
        num_objective_function_configs = len(objective_function_named_configs)



        named_optimizer_config = optimizer_named_configs[test_num % num_optimizer_configs]
        named_objective_function_config = objective_function_named_configs[test_num % num_objective_function_configs]

        self.logger.info("#####################################################################################################")
        self.logger.info(named_optimizer_config)
        self.logger.info(named_objective_function_config)

        optimizer_evaluator_config = optimizer_evaluator_config_store.get_config_by_name(name="parallel_unit_tests_config")
        optimizer_config = named_optimizer_config.config_point
        objective_function_config = named_objective_function_config.config_point

        optimizer_evaluator = OptimizerEvaluator(
            optimizer_evaluator_config=optimizer_evaluator_config,
            objective_function_config=objective_function_config,
            optimizer_config=optimizer_config
        )

        optimizer_evaluation_report = optimizer_evaluator.evaluate_optimizer()

        mlos.global_values.tracer.trace_events.extend(optimizer_evaluation_report.execution_trace)
        if not optimizer_evaluation_report.success:
            raise optimizer_evaluation_report.exception

        for objective_name, single_objective_fit_state in optimizer_evaluation_report.regression_model_fit_state:
            with pd.option_context('display.max_columns', 100):
                self.logger.info(single_objective_fit_state.get_goodness_of_fit_dataframe(DataSetType.TRAIN).tail())
                for optimum_name, optimum_over_time in optimizer_evaluation_report.optima_over_time.items():
                    self.logger.info("#####################################################################################################")
                    self.logger.info(optimum_name)
                    self.logger.info(optimum_over_time.get_dataframe().tail(10))
                    self.logger.info("#####################################################################################################")

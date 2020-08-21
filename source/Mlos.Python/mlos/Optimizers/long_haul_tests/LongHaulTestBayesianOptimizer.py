#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import math
import os
import random
import unittest

import numpy as np
import pandas as pd

from mlos.Logger import create_logger
from mlos.Tracer import Tracer

from mlos.Optimizers.BayesianOptimizer import BayesianOptimizer, BayesianOptimizerConfig
from mlos.Optimizers.OptimizationProblem import OptimizationProblem, Objective
from mlos.Spaces import SimpleHypergrid, ContinuousDimension

from mlos.SynthethicFunctions.sample_functions import quadratic
from mlos.SynthethicFunctions.HierarchicalFunctions import MultilevelQuadratic

import mlos.global_values as global_values

class TestBayesianOptimizer(unittest.TestCase):
    """ Tests if the random search optimizer can work with a lot of random configs and a ton of samples.

    """

    @classmethod
    def setUpClass(cls):
        """ Set's up all the objects needed to test the RandomSearchOptimizer

        To test the RandomSearchOptimizer we need to first construct:
        * an optimization problem
        * a utility function

        To construct a utility function we need the same set up as in the TestConfidenceBoundUtilityFunction
        test.



        :return:
        """

        cls.temp_dir = os.path.join(os.getcwd(), "temp")
        if not os.path.exists(cls.temp_dir):
            os.mkdir(cls.temp_dir)

        global_values.declare_singletons()
        global_values.tracer = Tracer(actor_id=cls.__name__, thread_id=0)
        cls.logger = create_logger(logger_name=cls.__name__)

    @classmethod
    def tearDownClass(cls) -> None:
        trace_output_path = os.path.join(cls.temp_dir, "OptimizerTestTrace.json")
        global_values.tracer.dump_trace_to_file(output_file_path=trace_output_path)

    def test_bayesian_optimizer_on_simple_2d_quadratic_function_pre_heated(self):
        """ Tests the bayesian optimizer on a simple quadratic function first feeding the optimizer a lot of data.

        :return:
        """
        input_space = SimpleHypergrid(
            name="input",
            dimensions=[
                ContinuousDimension(name='x_1', min=-100, max=100),
                ContinuousDimension(name='x_2', min=-100, max=100)
            ]
        )

        output_space = SimpleHypergrid(
            name="output",
            dimensions=[
                ContinuousDimension(name='y', min=-math.inf, max=math.inf)
            ]
        )

        x_1, x_2 = np.meshgrid(
            input_space['x_1'].linspace(num=501),
            input_space['x_2'].linspace(num=501)
        )

        y = quadratic(x_1=x_1, x_2=x_2)

        input_values_dataframe = pd.DataFrame({'x_1': x_1.reshape(-1), 'x_2': x_2.reshape(-1)})
        output_values_dataframe = pd.DataFrame({'y': y.reshape(-1)})

        optimization_problem = OptimizationProblem(
            parameter_space=input_space,
            objective_space=output_space,
            objectives=[Objective(name='y', minimize=True)]
        )

        bayesian_optimizer = BayesianOptimizer(
            optimization_problem=optimization_problem,
            optimizer_config=BayesianOptimizerConfig.DEFAULT,
            logger=self.logger
        )
        bayesian_optimizer.register(input_values_dataframe, output_values_dataframe)

        num_guided_samples = 20
        for i in range(num_guided_samples):
            # Suggest the parameters
            suggested_params = bayesian_optimizer.suggest()
            suggested_params_dict = suggested_params.to_dict()

            # Reformat them to feed the parameters to the target
            target_value = quadratic(**suggested_params_dict)
            self.logger.info(f"[{i}/{num_guided_samples}] suggested params: {suggested_params}, target: {target_value}")

            # Reformat the observation to feed it back to the optimizer
            input_values_df = pd.DataFrame({param_name: [param_value] for param_name, param_value in suggested_params_dict.items()})
            target_values_df = pd.DataFrame({'y': [target_value]})

            # Register the observation with the optimizer
            bayesian_optimizer.register(input_values_df, target_values_df)

        self.logger.info(f"Optimum: {bayesian_optimizer.optimum()}")
        trace_output_path = os.path.join(self.temp_dir, "PreHeatedTrace.json")
        self.logger.info(f"Writing trace to {trace_output_path}")
        global_values.tracer.dump_trace_to_file(output_file_path=trace_output_path)
        global_values.tracer.clear_events()

    def test_bayesian_optimizer_on_simple_2d_quadratic_function_cold_start(self):
        """ Tests the bayesian optimizer on a simple quadratic function with no prior data.

        :return:
        """
        input_space = SimpleHypergrid(
            name="input",
            dimensions=[
                ContinuousDimension(name='x_1', min=-100, max=100),
                ContinuousDimension(name='x_2', min=-100, max=100)
            ]
        )

        output_space = SimpleHypergrid(
            name="output",
            dimensions=[
                ContinuousDimension(name='y', min=-math.inf, max=math.inf)
            ]
        )

        optimization_problem = OptimizationProblem(
            parameter_space=input_space,
            objective_space=output_space,
            objectives=[Objective(name='y', minimize=True)]
        )

        bayesian_optimizer = BayesianOptimizer(
            optimization_problem=optimization_problem,
            optimizer_config=BayesianOptimizerConfig.DEFAULT,
            logger=self.logger
        )

        num_guided_samples = 1000
        for i in range(num_guided_samples):
            suggested_params = bayesian_optimizer.suggest()
            suggested_params_dict = suggested_params.to_dict()

            target_value = quadratic(**suggested_params_dict)
            self.logger.info(f"[{i}/{num_guided_samples}] suggested params: {suggested_params}, target: {target_value}")

            input_values_df = pd.DataFrame({param_name: [param_value] for param_name, param_value in suggested_params_dict.items()})
            target_values_df = pd.DataFrame({'y': [target_value]})

            bayesian_optimizer.register(input_values_df, target_values_df)
            if i > 20 and i % 20 == 0:
                self.logger.info(f"[{i}/{num_guided_samples}] Optimum: {bayesian_optimizer.optimum()}")

        self.logger.info(f"Optimum: {bayesian_optimizer.optimum()}")

    @unittest.skip(reason="Takes a while and it just ran. TODO: unskip.")
    def test_hierarchical_quadratic_cold_start(self):

        output_space = SimpleHypergrid(
            name="output",
            dimensions=[
                ContinuousDimension(name='y', min=-math.inf, max=math.inf)
            ]
        )

        optimization_problem = OptimizationProblem(
            parameter_space=MultilevelQuadratic.CONFIG_SPACE,
            objective_space=output_space,
            objectives=[Objective(name='y', minimize=True)]
        )

        num_restarts = 1000
        for restart_num in range(num_restarts):
            bayesian_optimizer = BayesianOptimizer(
                optimization_problem=optimization_problem,
                optimizer_config=BayesianOptimizerConfig.DEFAULT,
                logger=self.logger
            )

            num_guided_samples = 200
            for i in range(num_guided_samples):
                suggested_params = bayesian_optimizer.suggest()
                y = MultilevelQuadratic.evaluate(suggested_params)
                self.logger.info(f"[{i}/{num_guided_samples}] {suggested_params}, y: {y}")

                input_values_df = pd.DataFrame({
                    param_name: [param_value]
                    for param_name, param_value in suggested_params
                })
                target_values_df = pd.DataFrame({'y': [y]})
                bayesian_optimizer.register(input_values_df, target_values_df)

            self.logger.info(f"[{restart_num}/{num_restarts}] Optimum: {bayesian_optimizer.optimum()}")

    @unittest.skip(reason="Takes a while and it just ran. TODO: unskip.")
    def test_hierarchical_quadratic_cold_start_random_configs(self):

        output_space = SimpleHypergrid(
            name="output",
            dimensions=[
                ContinuousDimension(name='y', min=-math.inf, max=math.inf)
            ]
        )

        optimization_problem = OptimizationProblem(
            parameter_space=MultilevelQuadratic.CONFIG_SPACE,
            objective_space=output_space,
            objectives=[Objective(name='y', minimize=True)]
        )

        random_state = random.Random()
        num_restarts = 100
        has_failed = False
        for restart_num in range(num_restarts):
            try:
                # Let's set up random seeds so that we can easily repeat failed experiments
                #
                random_state.seed(restart_num)
                BayesianOptimizerConfig.CONFIG_SPACE.random_state = random_state
                MultilevelQuadratic.CONFIG_SPACE.random_state = random_state

                optimizer_config = BayesianOptimizerConfig.CONFIG_SPACE.random()
                self.logger.info(f"[Restart: {restart_num}/{num_restarts}] Creating a BayesianOptimimizer with the following config: ")
                self.logger.info(f"Optimizer config: {optimizer_config.to_json(indent=2)}")
                bayesian_optimizer = BayesianOptimizer(
                    optimization_problem=optimization_problem,
                    optimizer_config=optimizer_config,
                    logger=self.logger
                )

                num_guided_samples = optimizer_config.min_samples_required_for_guided_design_of_experiments + 50
                for i in range(num_guided_samples):
                    suggested_params = bayesian_optimizer.suggest()
                    y = MultilevelQuadratic.evaluate(suggested_params)
                    self.logger.info(f"[Restart: {restart_num}/{num_restarts}][Sample: {i}/{num_guided_samples}] {suggested_params}, y: {y}")

                    input_values_df = pd.DataFrame({
                        param_name: [param_value]
                        for param_name, param_value in suggested_params
                    })
                    target_values_df = pd.DataFrame({'y': [y]})
                    bayesian_optimizer.register(input_values_df, target_values_df)

                self.logger.info(f"[Restart: {restart_num}/{num_restarts}] Optimum: {bayesian_optimizer.optimum()}")
            except Exception as e:
                has_failed = True
                error_file_path = os.path.join(os.getcwd(), "temp", "test_errors.txt")
                with open(error_file_path, 'a') as out_file:
                    out_file.write("##################################################################################\n")
                    out_file.write(f"{restart_num} failed.\n")
                    out_file.write(f"Exception: {e}")
        self.assertFalse(has_failed)

#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import math
import unittest
import warnings

import grpc
import pandas as pd

import mlos.global_values as global_values
from mlos.Grpc.BayesianOptimizerFactory import BayesianOptimizerFactory
from mlos.Grpc.OptimizerMicroserviceServer import OptimizerMicroserviceServer
from mlos.Grpc.OptimizerMonitor import OptimizerMonitor
from mlos.Logger import create_logger
from mlos.Optimizers.BayesianOptimizer import BayesianOptimizerConfig
from mlos.Optimizers.OptimizationProblem import OptimizationProblem, Objective
from mlos.Spaces import ContinuousDimension, SimpleHypergrid
from mlos.SynthethicFunctions.sample_functions import quadratic


class TestBayesianOptimizerGrpcClient(unittest.TestCase):
    """ Tests the E2E Grpc Client-Service workflow.

    """

    @classmethod
    def setUpClass(cls):
        warnings.simplefilter("error")
        global_values.declare_singletons()

    def setUp(self):
        self.logger = create_logger(self.__class__.__name__)
        # Start up the gRPC service.
        #
        self.server = OptimizerMicroserviceServer(port=50051, num_threads=10)
        self.server.start()

        self.optimizer_service_channel = grpc.insecure_channel('localhost:50051')
        self.bayesian_optimizer_factory = BayesianOptimizerFactory(grpc_channel=self.optimizer_service_channel, logger=self.logger)
        self.optimizer_monitor = OptimizerMonitor(grpc_channel=self.optimizer_service_channel, logger=self.logger)

        # Define the optimization problem.
        #
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

        self.optimization_problem = OptimizationProblem(
            parameter_space=input_space,
            objective_space=output_space,
            objectives=[Objective(name='y', minimize=True)]
        )



    def tearDown(self):
        """ We need to tear down the gRPC server here.

        :return:
        """
        self.server.stop(grace=None)

    def test_optimizer_with_default_config(self):
        pre_existing_optimizers = {optimizer.id: optimizer for optimizer in self.optimizer_monitor.get_existing_optimizers()}
        bayesian_optimizer = self.bayesian_optimizer_factory.create_remote_optimizer(
            optimization_problem=self.optimization_problem,
            optimizer_config=BayesianOptimizerConfig.DEFAULT
        )
        post_existing_optimizers = {optimizer.id: optimizer for optimizer in self.optimizer_monitor.get_existing_optimizers()}

        new_optimizers = {
            optimizer_id: optimizer
            for optimizer_id, optimizer in post_existing_optimizers.items()
            if optimizer_id not in pre_existing_optimizers
        }

        self.assertTrue(len(new_optimizers) == 1)

        new_optimizer_id = list(new_optimizers.keys())[0]
        new_optimizer = new_optimizers[new_optimizer_id]

        self.assertTrue(new_optimizer_id == bayesian_optimizer.id)
        self.assertTrue(new_optimizer.optimizer_config == bayesian_optimizer.optimizer_config)

        self.optimize_quadratic(optimizer=bayesian_optimizer, num_iterations=100)

    def test_optimizer_with_random_config(self):
        for _ in range(10):
            optimizer_config = BayesianOptimizerConfig.CONFIG_SPACE.random()
            print(f"Creating a bayesian optimizer with config: {optimizer_config.to_dict()}")
            bayesian_optimizer = self.bayesian_optimizer_factory.create_remote_optimizer(
                optimization_problem=self.optimization_problem,
                optimizer_config=optimizer_config
            )
            self.optimize_quadratic(optimizer=bayesian_optimizer, num_iterations=12)


    @unittest.skip(reason="Not implemented yet.")
    def test_optimizer_with_named_config(self):
        ...

    def optimize_quadratic(self, optimizer, num_iterations):
        for _ in range(num_iterations):
            params = optimizer.suggest()
            params_dict = params.to_dict()
            features_df = pd.DataFrame(params_dict, index=[0])

            prediction = optimizer.predict(features_df)
            prediction_df = prediction.get_dataframe()

            y = quadratic(**params_dict)
            print(f"Params: {params}, Actual: {y}, Prediction: {str(prediction_df)}")

            objectives_df = pd.DataFrame({'y': [y]})
            optimizer.register(features_df, objectives_df)

#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import pytest

from mlos.Grpc.OptimizerMonitoringServiceEncoderDecoder import OptimizerServiceDecoder, OptimizerServiceEncoder
from mlos.Optimizers.BayesianOptimizerFactory import BayesianOptimizerFactory
from mlos.Optimizers.BayesianOptimizer import BayesianOptimizer
from mlos.Grpc import OptimizerService_pb2
from mlos.Optimizers.OptimizationProblem import OptimizationProblem, Objective
from mlos.Spaces import CategoricalDimension, CompositeDimension, ContinuousDimension, DiscreteDimension, EmptyDimension, OrdinalDimension, SimpleHypergrid
from mlos.Optimizers.BayesianOptimizerConfigStore import bayesian_optimizer_config_store



class TestOptimizerServiceEncoderDecoder:

    def test_optimization_problem(self):
        parameter_space = SimpleHypergrid(
            name="test",
            dimensions=[
                ContinuousDimension(name="x",min=0,max=1),
                CategoricalDimension(name="y",values=[1,2,3])
            ]
        )
        objective_space = SimpleHypergrid(
            name="z",
            dimensions=[
                ContinuousDimension(name="z",min=0,max=1)
            ]
        )
        optimization_problem = OptimizationProblem(
            parameter_space=parameter_space,
            objective_space=objective_space,
            objectives=[
                Objective(name="z",minimize=True)   
            ]
        )
        encoded_problem = OptimizerServiceEncoder.encode_optimization_problem(optimization_problem)
        decoded_problem = OptimizerServiceDecoder.decode_optimization_problem(encoded_problem)
        
        # A = B iff A >= B && B <= A
        # Could be condensed to single loop but easier to read this way. 
        for _ in range(1000):
            assert decoded_problem.parameter_space.random() in parameter_space
        
        for _ in range(1000):
            assert parameter_space.random() in decoded_problem.parameter_space

        for _ in range(1000):
            assert decoded_problem.objective_space.random() in objective_space
        
        for _ in range(1000):
            assert objective_space.random() in decoded_problem.objective_space
        
        print(decoded_problem.objectives)
        assert len(decoded_problem.objectives) == 1
        assert decoded_problem.objectives[0].name=="z"
        assert decoded_problem.objectives[0].minimize





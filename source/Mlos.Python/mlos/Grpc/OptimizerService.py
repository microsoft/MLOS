# pylint: disable=unused-argument
#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import json

import pandas as pd

from mlos.Grpc import OptimizerService_pb2, OptimizerService_pb2_grpc, MlosCommonMessageTypes_pb2
from mlos.MlosOptimizationServices.BayesianOptimizerStore.BayesianOptimizerStoreBase import BayesianOptimizerStoreBase
from mlos.Optimizers.BayesianOptimizer import BayesianOptimizer, bayesian_optimizer_config_store
from mlos.Optimizers.OptimizationProblem import OptimizationProblem
from mlos.Spaces import Point
from mlos.Logger import create_logger



class OptimizerService(OptimizerService_pb2_grpc.OptimizerServiceServicer):
    """ Defines the Optimizer Microservice.

    The state of the microservice will be persisted in a DB. Until then we use local variables.

    """

    def __init__(self, bayesian_optimizer_store: BayesianOptimizerStoreBase, logger=None):
        self._bayesian_optimizer_store = bayesian_optimizer_store
        if logger is None:
            logger = create_logger(self.__class__.__name__)
        self.logger = logger

    def CreateOptimizer(self, request: OptimizerService_pb2.CreateOptimizerRequest, context): # pylint: disable=unused-argument
        self.logger.info("Creating Optimizer")
        optimization_problem = OptimizationProblem.from_protobuf(optimization_problem_pb2=request.OptimizationProblem)
        optimizer_config_json = request.OptimizerConfig
        if optimizer_config_json is not None and len(optimizer_config_json) > 0:
            optimizer_config = Point.from_json(optimizer_config_json)
        else:
            optimizer_config = bayesian_optimizer_config_store.default

        optimizer = BayesianOptimizer(
            optimization_problem=optimization_problem,
            optimizer_config=optimizer_config
        )

        optimizer_id = self._bayesian_optimizer_store.get_next_optimizer_id()
        self._bayesian_optimizer_store.add_optimizer(optimizer_id=optimizer_id, optimizer=optimizer)

        self.logger.info(f"Created optimizer {optimizer_id} with config: {optimizer.optimizer_config.to_json(indent=2)}")
        return MlosCommonMessageTypes_pb2.OptimizerHandle(Id=optimizer_id)

    def Suggest(self, request, context): # pylint: disable=unused-argument
        self.logger.info("Suggesting")

        # TODO: return an error if optimizer not found
        #
        if request.Context.ContextJsonString != "":
            raise NotImplementedError("Context not currently supported in remote optimizers")
        with self._bayesian_optimizer_store.exclusive_optimizer(optimizer_id=request.OptimizerHandle.Id) as optimizer:
            # TODO handle context here
            suggested_params = optimizer.suggest(random=request.Random)

        return MlosCommonMessageTypes_pb2.ConfigurationParameters(
            ParametersJsonString=json.dumps(suggested_params.to_dict())
        )

    def RegisterObservation(self, request, context): # pylint: disable=unused-argument
        # TODO: add an API to register observations in bulk.
        # TODO: stop ignoring context
        #
        feature_values = json.loads(request.Observation.Features.FeaturesJsonString)
        feature_values_dataframe = pd.DataFrame(feature_values, index=[0])

        objective_values = json.loads(request.Observation.ObjectiveValues.ObjectiveValuesJsonString)
        objective_values_dataframe = pd.DataFrame(objective_values, index=[0])

        with self._bayesian_optimizer_store.exclusive_optimizer(optimizer_id=request.OptimizerHandle.Id) as optimizer:
            optimizer.register(parameter_values_pandas_frame=feature_values_dataframe, target_values_pandas_frame=objective_values_dataframe)

        return MlosCommonMessageTypes_pb2.Empty()

    def RegisterObservations(self, request, context): # pylint: disable=unused-argument
        # TODO: stop ignoring context
        #
        observations = request.Observations
        features_df = pd.read_json(observations.Features.FeaturesJsonString, orient='index')
        objectives_df = pd.read_json(observations.ObjectiveValues.ObjectiveValuesJsonString, orient='index')

        with self._bayesian_optimizer_store.exclusive_optimizer(optimizer_id=request.OptimizerHandle.Id) as optimizer:
            optimizer.register(parameter_values_pandas_frame=features_df, target_values_pandas_frame=objectives_df)

        return MlosCommonMessageTypes_pb2.Empty()

    def Echo(self, request: MlosCommonMessageTypes_pb2.Empty, context): # pylint: disable=unused-argument
        return MlosCommonMessageTypes_pb2.Empty()

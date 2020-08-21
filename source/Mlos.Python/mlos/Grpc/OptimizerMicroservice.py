# pylint: disable=unused-argument
#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import json
import logging
import pandas as pd

from mlos.Grpc import OptimizerService_pb2, OptimizerService_pb2_grpc
from mlos.Grpc.OptimizerService_pb2 import Empty, OptimizerInfo, OptimizerHandle, OptimizerList
from mlos.Optimizers.BayesianOptimizer import BayesianOptimizer, BayesianOptimizerConfig
from mlos.Optimizers.OptimizationProblem import OptimizationProblem


class OptimizerMicroservice(OptimizerService_pb2_grpc.OptimizerServiceServicer):
    """ Defines the Optimizer Microservice.

    The state of the microservice will be persisted in a DB. Until then we use local variables.

    """

    def __init__(self):
        self._next_optimizer_id = 0
        self._optimizers_by_id = dict()

    def get_next_optimizer_id(self):
        self._next_optimizer_id += 1
        return str(self._next_optimizer_id - 1)

    def ListExistingOptimizers(self, request: Empty, context):
        optimizers_info = []
        for optimizer_id, optimizer in self._optimizers_by_id.items():
            optimizers_info.append(OptimizerInfo(
                OptimizerHandle=OptimizerHandle(Id=optimizer_id),
                OptimizerConfigJsonString=optimizer.optimizer_config.to_json(),
                OptimizationProblem=optimizer.optimization_problem.to_protobuf()
            ))
        return OptimizerList(Optimizers=optimizers_info)

    def GetOptimizerInfo(self, request: OptimizerHandle, context):
        # TODO: Learn about and leverage gRPC's error handling model for a case
        # TODO: when the handle is invalid.
        optimizer = self._optimizers_by_id[request.Id]
        return OptimizerInfo(
            OptimizerHandle=OptimizerHandle(Id=request.Id),
            OptimizerConfigJsonString=optimizer.optimizer_config.to_json(),
            OptimizationProblem=optimizer.optimization_problem.to_protobuf()
        )

    def CreateOptimizer(self, request: OptimizerService_pb2.CreateOptimizerRequest, context): # pylint: disable=unused-argument

        optimization_problem = OptimizationProblem.from_protobuf(optimization_problem_pb2=request.OptimizationProblem)

        optimizer = BayesianOptimizer(
            optimization_problem=optimization_problem,
            optimizer_config=BayesianOptimizerConfig.DEFAULT
        )

        optimizer_id = self.get_next_optimizer_id()
        self._optimizers_by_id[optimizer_id] = optimizer
        logging.info(f"Created optimizer {optimizer_id}.")
        return OptimizerService_pb2.OptimizerHandle(Id=optimizer_id)

    def Suggest(self, request, context): # pylint: disable=unused-argument
        # TODO: return an error if optimizer not found
        #
        optimizer = self._get_optimizer(request)
        suggested_params = optimizer.suggest(random=request.Random, context=request.Context)
        return OptimizerService_pb2.ConfigurationParameters(
            ParametersJsonString=json.dumps(suggested_params.to_dict())
        )

    def RegisterObservation(self, request, context): # pylint: disable=unused-argument
        # TODO: add an API to register observations in bulk.
        # TODO: stop ignoring context
        #
        optimizer = self._get_optimizer(request)
        feature_values = json.loads(request.Observation.Features.FeaturesJsonString)
        feature_values_dataframe = pd.DataFrame(feature_values, index=[0])

        objective_values = json.loads(request.Observation.ObjectiveValues.ObjectiveValuesJsonString)
        objective_values_dataframe = pd.DataFrame(objective_values, index=[0])

        optimizer.register(feature_values_dataframe, objective_values_dataframe)

        return Empty()

    def Predict(self, request, context): # pylint: disable=unused-argument
        optimizer = self._get_optimizer(request)
        features_dict = json.loads(request.Features.FeaturesJsonString)
        features_df = pd.DataFrame(features_dict)

        predictions = optimizer.predict(features_df)

        if not isinstance(predictions, list):
            # a single objective optimization problem is executing, so create list of one prediction
            predictions = [predictions]

        response = OptimizerService_pb2.PredictResponse(
            ObjectivePredictions=[
                OptimizerService_pb2.SingleObjectivePrediction(
                    ObjectiveName=prediction.objective_name,
                    PredictionDataframeJsonString=prediction.dataframe_to_json()
                )
                for prediction in predictions
            ]
        )

        return response

    def _get_optimizer(self, request):
        # TODO: throw exceptions if invalid Id, or invalid Request
        return self._optimizers_by_id[request.OptimizerHandle.Id]

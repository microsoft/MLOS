# pylint: disable=unused-argument
#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import json

import pandas as pd

from mlos.global_values import serialize_to_bytes_string
from mlos.Grpc.OptimizerMonitoringService_pb2_grpc import OptimizerMonitoringServiceServicer
from mlos.Grpc.OptimizerMonitoringService_pb2 import OptimizerConvergenceState, OptimizerList, PredictResponse, SingleObjectivePrediction, Empty, \
    OptimizerInfo, OptimizerHandle, Observations, Features, ObjectiveValues, SimpleBoolean, SimpleString
from mlos.Grpc.OptimizerMonitoringServiceEncoderDecoder import OptimizerMonitoringServiceEncoder
from mlos.MlosOptimizationServices.BayesianOptimizerStore.BayesianOptimizerStoreBase import BayesianOptimizerStoreBase
from mlos.Optimizers.RegressionModels.Prediction import Prediction
from mlos.Logger import create_logger



class OptimizerMonitoringService(OptimizerMonitoringServiceServicer):
    """ Defines the Optimizer Microservice.

    The state of the microservice will be persisted in a DB. Until then we use local variables.

    """

    def __init__(self, bayesian_optimizer_store: BayesianOptimizerStoreBase, logger=None):
        self._bayesian_optimizer_store = bayesian_optimizer_store
        if logger is None:
            logger = create_logger(self.__class__.__name__)
        self.logger = logger

    def ListExistingOptimizers(self, request: Empty, context):
        optimizers_info = []
        for optimizer_id, optimizer in self._bayesian_optimizer_store.list_optimizers():
            optimizers_info.append(OptimizerInfo(
                OptimizerHandle=OptimizerHandle(Id=optimizer_id),
                OptimizerConfigJsonString=optimizer.optimizer_config.to_json(),
                OptimizationProblem=OptimizerMonitoringServiceEncoder.encode_optimization_problem(optimizer.optimization_problem)
            ))
        return OptimizerList(Optimizers=optimizers_info)

    def GetOptimizerInfo(self, request: OptimizerHandle, context):
        # TODO: Learn about and leverage gRPC's error handling model for a case
        # TODO: when the handle is invalid.
        optimizer_id = request.Id
        optimizer = self._bayesian_optimizer_store.get_optimizer(optimizer_id)
        return OptimizerInfo(
            OptimizerHandle=OptimizerHandle(Id=request.Id),
            OptimizerConfigJsonString=optimizer.optimizer_config.to_json(),
            OptimizationProblem=OptimizerMonitoringServiceEncoder.encode_optimization_problem(optimizer.optimization_problem)
        )

    def GetOptimizerConvergenceState(self, request, context):
        with self._bayesian_optimizer_store.exclusive_optimizer(optimizer_id=request.Id) as optimizer:
            serialized_convergence_state = serialize_to_bytes_string(optimizer.get_optimizer_convergence_state())

        return OptimizerConvergenceState(
            OptimizerHandle=OptimizerHandle(Id=request.Id),
            SerializedOptimizerConvergenceState=serialized_convergence_state
        )

    def IsTrained(self, request, context): # pylint: disable=unused-argument
        with self._bayesian_optimizer_store.exclusive_optimizer(optimizer_id=request.Id) as optimizer:
            is_trained = optimizer.trained
        return SimpleBoolean(Value=is_trained)

    def ComputeGoodnessOfFitMetrics(self, request, context):
        with self._bayesian_optimizer_store.exclusive_optimizer(optimizer_id=request.Id) as optimizer:
            gof_metrics = optimizer.compute_surrogate_model_goodness_of_fit()
        return SimpleString(Value=gof_metrics.to_json())

    def GetAllObservations(self, request, context): # pylint: disable=unused-argument
        with self._bayesian_optimizer_store.exclusive_optimizer(optimizer_id=request.Id) as optimizer:
            features_df, objectives_df, _ = optimizer.get_all_observations()

        return Observations(
            Features=Features(FeaturesJsonString=features_df.to_json(orient='index', double_precision=15)),
            ObjectiveValues=ObjectiveValues(ObjectiveValuesJsonString=objectives_df.to_json(orient='index', double_precision=15))
        )

    def Predict(self, request, context): # pylint: disable=unused-argument

        features_dict = json.loads(request.Features.FeaturesJsonString)
        features_df = pd.DataFrame(features_dict)
        with self._bayesian_optimizer_store.exclusive_optimizer(optimizer_id=request.OptimizerHandle.Id) as optimizer:
            prediction = optimizer.predict(features_df)
        assert isinstance(prediction, Prediction)

        response = PredictResponse(
            ObjectivePredictions=[
                SingleObjectivePrediction(
                    ObjectiveName=prediction.objective_name,
                    PredictionDataFrameJsonString=prediction.dataframe_to_json()
                )
            ]
        )

        return response

    def Echo(self, request: Empty, context): # pylint: disable=unused-argument
        return Empty()

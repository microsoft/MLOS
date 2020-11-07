# pylint: disable=unused-argument
#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import uuid
from contextlib import contextmanager
import json
import multiprocessing
from typing import Iterator

import pandas as pd

from mlos.global_values import serialize_to_bytes_string
from mlos.Grpc import OptimizerService_pb2, OptimizerService_pb2_grpc
from mlos.Grpc.OptimizerService_pb2 import Empty, OptimizerConvergenceState, OptimizerInfo, OptimizerHandle, OptimizerList, Observations, Features,\
    ObjectiveValues, SimpleBoolean, SimpleString
from mlos.Optimizers.BayesianOptimizer import BayesianOptimizer, bayesian_optimizer_config_store
from mlos.Optimizers.OptimizationProblem import OptimizationProblem
from mlos.Optimizers.RegressionModels.Prediction import Prediction
from mlos.Spaces import Point
from mlos.Logger import create_logger



class OptimizerMicroservice(OptimizerService_pb2_grpc.OptimizerServiceServicer):
    """ Defines the Optimizer Microservice.

    The state of the microservice will be persisted in a DB. Until then we use local variables.

    """

    def __init__(self):
        self._optimizers_by_id = dict()
        self._ordered_ids = []

        self._lock_manager = multiprocessing.Manager()
        self._optimizer_locks_by_optimizer_id = dict()
        self.logger = create_logger("OptimizerMicroservice")
        self.logger.info("OptimizerMicroservice init")

    @staticmethod
    def get_next_optimizer_id():
        return str(uuid.uuid4())

    @contextmanager
    def exclusive_optimizer(self, optimizer_id) -> Iterator[BayesianOptimizer]:
        """ Context manager to acquire the optimizer lock and yield the corresponding optimizer.

        This makes sure that:
            1. The lock is acquired before any operation on the optimizer commences.
            2. The lock is released even if exceptions are flying.


        :param optimizer_id:
        :return:
        :raises: KeyError if the optimizer_id was not found.
        """
        with self._optimizer_locks_by_optimizer_id[optimizer_id]:
            yield self._optimizers_by_id[optimizer_id]

    def ListExistingOptimizers(self, request: Empty, context):
        optimizers_info = []
        for optimizer_id in self._ordered_ids:
            optimizer = self._optimizers_by_id[optimizer_id]
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

    def GetOptimizerConvergenceState(self, request, context):
        with self.exclusive_optimizer(optimizer_id=request.Id) as optimizer:
            serialized_convergence_state = serialize_to_bytes_string(optimizer.get_optimizer_convergence_state())

        return OptimizerConvergenceState(
            OptimizerHandle=OptimizerHandle(Id=request.Id),
            SerializedOptimizerConvergenceState=serialized_convergence_state
        )

    def CreateOptimizer(self, request: OptimizerService_pb2.CreateOptimizerRequest, context): # pylint: disable=unused-argument
        self.logger.info("Creating Optimizer")
        print("CREATING OPTIMIZER")
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

        optimizer_id = self.get_next_optimizer_id()

        # To avoid a race condition we acquire the lock before inserting the lock and the optimizer into their respective
        # dictionaries. Otherwise we could end up with a situation where a lock is in the dictionary, but the optimizer
        # is not.
        optimizer_lock = self._lock_manager.RLock()
        with optimizer_lock:
            self._optimizer_locks_by_optimizer_id[optimizer_id] = optimizer_lock
            self._optimizers_by_id[optimizer_id] = optimizer
            self._ordered_ids.append(optimizer_id)
        self.logger.info(f"Created optimizer {optimizer_id}.")
        return OptimizerService_pb2.OptimizerHandle(Id=optimizer_id)

    def IsTrained(self, request, context): # pylint: disable=unused-argument
        with self.exclusive_optimizer(optimizer_id=request.Id) as optimizer:
            is_trained = optimizer.trained
        return SimpleBoolean(Value=is_trained)

    def ComputeGoodnessOfFitMetrics(self, request, context):
        with self.exclusive_optimizer(optimizer_id=request.Id) as optimizer:
            gof_metrics = optimizer.compute_surrogate_model_goodness_of_fit()
        return SimpleString(Value=gof_metrics.to_json())

    def Suggest(self, request, context): # pylint: disable=unused-argument
        self.logger.info("Suggesting")

        # TODO: return an error if optimizer not found
        #
        with self.exclusive_optimizer(optimizer_id=request.OptimizerHandle.Id) as optimizer:
            suggested_params = optimizer.suggest(random=request.Random, context=request.Context)

        return OptimizerService_pb2.ConfigurationParameters(
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

        with self.exclusive_optimizer(optimizer_id=request.OptimizerHandle.Id) as optimizer:
            optimizer.register(feature_values_pandas_frame=feature_values_dataframe, target_values_pandas_frame=objective_values_dataframe)

        return Empty()

    def RegisterObservations(self, request, context): # pylint: disable=unused-argument
        # TODO: stop ignoring context
        #
        observations = request.Observations
        features_df = pd.read_json(observations.Features.FeaturesJsonString, orient='index')
        objectives_df = pd.read_json(observations.ObjectiveValues.ObjectiveValuesJsonString, orient='index')

        with self.exclusive_optimizer(optimizer_id=request.OptimizerHandle.Id) as optimizer:
            optimizer.register(feature_values_pandas_frame=features_df, target_values_pandas_frame=objectives_df)

        return Empty()

    def GetAllObservations(self, request, context): # pylint: disable=unused-argument
        with self.exclusive_optimizer(optimizer_id=request.Id) as optimizer:
            features_df, objectives_df = optimizer.get_all_observations()

        return Observations(
            Features=Features(FeaturesJsonString=features_df.to_json(orient='index', double_precision=15)),
            ObjectiveValues=ObjectiveValues(ObjectiveValuesJsonString=objectives_df.to_json(orient='index', double_precision=15))
        )


    def Predict(self, request, context): # pylint: disable=unused-argument

        features_dict = json.loads(request.Features.FeaturesJsonString)
        features_df = pd.DataFrame(features_dict)
        with self.exclusive_optimizer(optimizer_id=request.OptimizerHandle.Id) as optimizer:
            prediction = optimizer.predict(features_df)
        assert isinstance(prediction, Prediction)

        response = OptimizerService_pb2.PredictResponse(
            ObjectivePredictions=[
                OptimizerService_pb2.SingleObjectivePrediction(
                    ObjectiveName=prediction.objective_name,
                    PredictionDataFrameJsonString=prediction.dataframe_to_json()
                )
            ]
        )

        return response

    def Echo(self, request: Empty, context): # pylint: disable=unused-argument
        return Empty()

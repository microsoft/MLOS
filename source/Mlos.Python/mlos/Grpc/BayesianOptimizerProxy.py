#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import json
from typing import Tuple

import pandas as pd

from mlos.global_values import deserialize_from_bytes_string
from mlos.Grpc import OptimizerMonitoringService_pb2
from mlos.Grpc.OptimizerMonitoringService_pb2_grpc import OptimizerMonitoringServiceStub
from mlos.Grpc import OptimizerService_pb2
from mlos.Grpc.OptimizerService_pb2_grpc import OptimizerServiceStub
from mlos.Logger import create_logger
from mlos.Optimizers.OptimizerBase import OptimizerBase
from mlos.Optimizers.RegressionModels.MultiObjectiveGoodnessOfFitMetrics import MultiObjectiveGoodnessOfFitMetrics
from mlos.Optimizers.RegressionModels.Prediction import Prediction
from mlos.Spaces import Point
from mlos.Tracer import trace

class BayesianOptimizerProxy(OptimizerBase):
    """ Client to remote BayesianOptimizer.

    Wraps all implementation details around communicating with the remote BayesianOptimizer.
    Benefits:
        * Simpler to use than making gRPC requests
        * We can change the gRPC definition without affecting the user's code.
        * All logic related to gRPC is in one place

    Parameters
    ----------
    grpc_channel : grpc_channel
        GRPC channel to connect to existing remote optimizer.
    optimization_problem : OptimizationProblem
        Problem to optimizer.
    optimizer_config : Point
        Optimizer Configuation.
    id : str
        Unique identifying string.
    logger : logger, default=None
        Logger to use. By default, a new logger is created internally.
    """

    def __init__(
            self,
            grpc_channel,
            optimization_problem,
            optimizer_config,
            id,  # pylint: disable=redefined-builtin
            logger=None
    ):
        if logger is None:
            logger = create_logger("BayesianOptimizerClient")
        self.logger = logger

        OptimizerBase.__init__(self, optimization_problem)
        assert optimizer_config is not None

        self._grpc_channel = grpc_channel
        self._optimizer_stub = OptimizerServiceStub(self._grpc_channel)
        self._optimizer_monitoring_stub = OptimizerMonitoringServiceStub(self._grpc_channel)
        self.optimizer_config = optimizer_config
        self.id = id

    @property
    def optimizer_handle_for_optimizer_monitoring_service(self):
        return OptimizerMonitoringService_pb2.OptimizerHandle(Id=self.id)

    @property
    def optimizer_handle_for_optimizer_service(self):
        return OptimizerService_pb2.OptimizerHandle(Id=self.id)

    @property
    def trained(self):
        response = self._optimizer_monitoring_stub.IsTrained(self.optimizer_handle_for_optimizer_monitoring_service)
        return response.Value

    @trace()
    def get_optimizer_convergence_state(self):
        optimizer_convergence_state_response = self._optimizer_monitoring_stub.GetOptimizerConvergenceState(
            self.optimizer_handle_for_optimizer_monitoring_service
        )
        return deserialize_from_bytes_string(optimizer_convergence_state_response.SerializedOptimizerConvergenceState)

    @trace()
    def compute_surrogate_model_goodness_of_fit(self):
        response = self._optimizer_monitoring_stub.ComputeGoodnessOfFitMetrics(self.optimizer_handle_for_optimizer_monitoring_service)
        return MultiObjectiveGoodnessOfFitMetrics.from_json(response.Value, objective_names=self.optimization_problem.objective_space.dimension_names)

    @trace()
    def suggest(self, random=False, context=None):  # pylint: disable=unused-argument
        if context is not None:
            raise NotImplementedError("Context not currently supported on remote optimizers")

        suggestion_request = OptimizerService_pb2.SuggestRequest(
            OptimizerHandle=self.optimizer_handle_for_optimizer_service,
            Random=random,
            Context=context
        )
        suggestion_response = self._optimizer_stub.Suggest(suggestion_request)
        suggested_params_dict = json.loads(suggestion_response.ParametersJsonString)
        return Point(**suggested_params_dict)

    @trace()
    def register(self, parameter_values_pandas_frame, target_values_pandas_frame, context_values_pandas_frame=None):
        if context_values_pandas_frame is not None:
            raise NotImplementedError("Context not currently supported on remote optimizers")

        feature_values_pandas_frame = parameter_values_pandas_frame
        register_request = OptimizerService_pb2.RegisterObservationsRequest(
            OptimizerHandle=self.optimizer_handle_for_optimizer_service,
            Observations=OptimizerService_pb2.Observations(
                Features=OptimizerService_pb2.Features(FeaturesJsonString=feature_values_pandas_frame.to_json(orient='index', double_precision=15)),
                ObjectiveValues=OptimizerService_pb2.ObjectiveValues(
                    ObjectiveValuesJsonString=target_values_pandas_frame.to_json(orient='index', double_precision=15)
                )
            )
        )
        self._optimizer_stub.RegisterObservations(register_request) # TODO: we should be using the optimizer_stub for this.

    @trace()
    def get_all_observations(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        response = self._optimizer_monitoring_stub.GetAllObservations(self.optimizer_handle_for_optimizer_monitoring_service)
        features_df = pd.read_json(response.Features.FeaturesJsonString, orient='index')
        objectives_df = pd.read_json(response.ObjectiveValues.ObjectiveValuesJsonString, orient='index')
        context_df = None
        return features_df, objectives_df, context_df

    @trace()
    def predict(self, parameter_values_pandas_frame, t=None, context_values_pandas_frame=None, objective_name=None) -> Prediction:  # pylint: disable=unused-argument
        # TODO: make this streaming and/or using arrow.
        #
        if context_values_pandas_frame is not None:
            raise NotImplementedError("Context not currently supported on remote optimizers")
        feature_values_dict = parameter_values_pandas_frame.to_dict(orient='list')
        prediction_request = OptimizerMonitoringService_pb2.PredictRequest(
            OptimizerHandle=self.optimizer_handle_for_optimizer_monitoring_service,
            Features=OptimizerMonitoringService_pb2.Features(
                FeaturesJsonString=json.dumps(feature_values_dict)
            )
        )
        prediction_response = self._optimizer_monitoring_stub.Predict(prediction_request)

        # To be compliant with the OptimizerBase, we need to recover a single Prediction object and return it.
        #
        objective_predictions_pb2 = prediction_response.ObjectivePredictions
        assert len(objective_predictions_pb2) == 1
        only_prediction_pb2 = objective_predictions_pb2[0]
        objective_name = only_prediction_pb2.ObjectiveName
        valid_predictions_df = Prediction.dataframe_from_json(only_prediction_pb2.PredictionDataFrameJsonString)
        prediction = Prediction.create_prediction_from_dataframe(objective_name=objective_name, dataframe=valid_predictions_df)
        return prediction

    def focus(self, subspace):  # pylint: disable=unused-argument,no-self-use
        pass

    def reset_focus(self):# pylint: disable=no-self-use
        pass

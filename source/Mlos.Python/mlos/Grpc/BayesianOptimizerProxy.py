#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import json

from mlos.Logger import create_logger
from mlos.Grpc import OptimizerService_pb2, OptimizerService_pb2_grpc
from mlos.Spaces import Point

from mlos.Optimizers.RegressionModels.Prediction import Prediction
from mlos.Optimizers.OptimizerInterface import OptimizerInterface


class BayesianOptimizerProxy(OptimizerInterface):
    """ Client to remote BayesianOptimizer.

    Wraps all implementation details around communicating with the remote BayesianOptimizer.
    Benefits:
        * Simpler to use than making gRPC requests
        * We can change the gRPC definition without affecting the user's code.
        * All logic related to gRPC is in one place
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

        OptimizerInterface.__init__(self, optimization_problem)
        assert optimizer_config is not None

        self._grpc_channel = grpc_channel
        self._optimizer_stub = OptimizerService_pb2_grpc.OptimizerServiceStub(self._grpc_channel)
        self.optimizer_config = optimizer_config
        self.id = id

    @property
    def optimizer_handle(self):
        return OptimizerService_pb2.OptimizerHandle(Id=self.id)

    def suggest(self, random=False, context=None):  # pylint: disable=unused-argument
        suggestion_request = OptimizerService_pb2.SuggestRequest(
            OptimizerHandle=self.optimizer_handle,
            Random=random
        )
        suggestion_response = self._optimizer_stub.Suggest(suggestion_request)
        suggested_params_dict = json.loads(suggestion_response.ParametersJsonString)
        return Point(**suggested_params_dict)

    def register(self, feature_values_pandas_frame, target_values_pandas_frame):  # pylint: disable=unused-argument
        # TODO: implement RegisterObservations <- plural
        #
        features_dicts_per_record = feature_values_pandas_frame.to_dict(orient='records')
        objectives_dicts_per_record = target_values_pandas_frame.to_dict(orient='records')

        # TODO: Either implement streaming or arrow flight or batch.
        #
        for feature_dict, objective_dict in zip(features_dicts_per_record, objectives_dicts_per_record):
            register_request = OptimizerService_pb2.RegisterObservationRequest(
                OptimizerHandle=self.optimizer_handle,
                Observation=OptimizerService_pb2.Observation(
                    Features=OptimizerService_pb2.Features(FeaturesJsonString=json.dumps(feature_dict)),
                    ObjectiveValues=OptimizerService_pb2.ObjectiveValues(ObjectiveValuesJsonString=json.dumps(objective_dict))
                )
            )
            self._optimizer_stub.RegisterObservation(register_request)

    def predict(self, feature_values_pandas_frame, t=None):  # pylint: disable=unused-argument
        # TODO: make this streaming and/or using arrow.
        #
        feature_values_dict = feature_values_pandas_frame.to_dict(orient='list')
        prediction_request = OptimizerService_pb2.PredictRequest(
            OptimizerHandle=self.optimizer_handle,
            Features=OptimizerService_pb2.Features(
                FeaturesJsonString=json.dumps(feature_values_dict)
            )
        )
        prediction_response = self._optimizer_stub.Predict(prediction_request)

        return [
            Prediction(
                target_name=prediction.ObjectiveName,
                mean=prediction.Mean,
                variance=prediction.Variance,
                count=prediction.ObservationCount,
                standard_deviation=prediction.StandardDeviation
            ) for prediction in prediction_response.ObjectivePredictions.Predictions
        ]

    def optimum(self, stay_focused=False):  # pylint: disable=unused-argument,no-self-use
        ...

    def focus(self, subspace):  # pylint: disable=unused-argument,no-self-use
        ...

    def reset_focus(self):# pylint: disable=no-self-use
        ...

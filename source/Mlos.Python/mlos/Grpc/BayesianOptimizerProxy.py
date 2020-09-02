#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import json
from typing import Tuple

import pandas as pd

from mlos.global_values import deserialize_from_bytes_string
from mlos.Grpc import OptimizerService_pb2, OptimizerService_pb2_grpc
from mlos.Logger import create_logger
from mlos.Optimizers.OptimizerInterface import OptimizerInterface
from mlos.Optimizers.RegressionModels.Prediction import Prediction
from mlos.Spaces import Point


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

    def get_optimizer_convergence_state(self):
        optimizer_convergence_state_response = self._optimizer_stub.GetOptimizerConvergenceState(self.optimizer_handle)
        return deserialize_from_bytes_string(optimizer_convergence_state_response.SerializedOptimizerConvergenceState)

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

    def get_all_observations(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        response = self._optimizer_stub.GetAllObservations(self.optimizer_handle)
        features_df = pd.read_json(response.Features.FeaturesJsonString, orient='index')
        objectives_df = pd.read_json(response.ObjectiveValues.ObjectiveValuesJsonString, orient='index')
        return features_df, objectives_df

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

        # To be compliant with the OptimizerInterface, we need to recover a single Prediction object and return it.
        #
        objective_predictions_pb2 = prediction_response.ObjectivePredictions
        assert len(objective_predictions_pb2) == 1
        only_prediction_pb2 = objective_predictions_pb2[0]
        objective_name = only_prediction_pb2.ObjectiveName
        valid_predictions_df = Prediction.dataframe_from_json(only_prediction_pb2.PredictionDataFrameJsonString)
        prediction = Prediction.create_prediction_from_dataframe(objective_name=objective_name, dataframe=valid_predictions_df)
        prediction.add_invalid_rows_at_missing_indices(desired_index=feature_values_pandas_frame.index)
        return prediction

    def optimum(self, stay_focused=False):  # pylint: disable=unused-argument,no-self-use
        ...

    def focus(self, subspace):  # pylint: disable=unused-argument,no-self-use
        ...

    def reset_focus(self):# pylint: disable=no-self-use
        ...

#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from typing import List
from mlos.Optimizers.RegressionModels.Prediction import Prediction

class MultiObjectivePrediction:
    """A container for multiple predictions.
    """
    def __init__(self, predictions: List[Prediction]):
        self.predictions_by_objective_name = {
            prediction.objective_name: prediction
            for prediction
            in predictions
        }
        self.predictions = predictions

    def __getitem__(self, item):
        if isinstance(item, str):
            return self.predictions_by_objective_name[item]
        elif isinstance(item, int):
            return self.predictions[item]
        else:
            raise KeyError("Key must be either an objective name or an integer.")

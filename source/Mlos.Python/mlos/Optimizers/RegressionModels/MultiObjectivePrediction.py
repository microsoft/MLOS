#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from typing import List, Union
from mlos.Utils.KeyOrderedDict import KeyOrderedDict
from mlos.Optimizers.RegressionModels.Prediction import Prediction

class MultiObjectivePrediction(KeyOrderedDict):
    """A container for multiple predictions.

    This is really just an alias to KeyOrderedDict.
    """

    def __init__(self, objective_names: List[str]):
        KeyOrderedDict.__init__(self, ordered_keys=objective_names, value_type=Prediction)

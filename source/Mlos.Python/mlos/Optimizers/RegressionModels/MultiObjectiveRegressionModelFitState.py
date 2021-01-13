#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from typing import List
from mlos.Optimizers.RegressionModels.RegressionModelFitState import RegressionModelFitState
from mlos.Utils.KeyOrderedDict import KeyOrderedDict

class MultiObjectiveRegressionModelFitState(KeyOrderedDict):
    """A container for multiple fit states.

    """

    def __init__(self, objective_names: List[str]):
        KeyOrderedDict.__init__(self, ordered_keys=objective_names, value_type=RegressionModelFitState)

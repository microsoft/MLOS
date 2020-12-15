#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from typing import List
from mlos.Utils.KeyOrderedDict import KeyOrderedDict
from mlos.Optimizers.RegressionModels.GoodnessOfFitMetrics import GoodnessOfFitMetrics

class MultiObjectiveGoodnessOfFitMetrics(KeyOrderedDict):
    """A container for multiple GoodnessOfFitMetrics.

    This is really just an alias to KeyOrderedDict.
    """

    def __init__(self, objective_names: List[str]):
        KeyOrderedDict.__init__(self, ordered_keys=objective_names, value_type=GoodnessOfFitMetrics)

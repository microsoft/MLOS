#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import json
from typing import List
from mlos.Utils.KeyOrderedDict import KeyOrderedDict
from mlos.Optimizers.RegressionModels.GoodnessOfFitMetrics import GoodnessOfFitMetrics

class MultiObjectiveGoodnessOfFitMetrics(KeyOrderedDict):
    """A container for multiple GoodnessOfFitMetrics.

    This is really just an alias to KeyOrderedDict.
    """

    def __init__(self, objective_names: List[str]):
        KeyOrderedDict.__init__(self, ordered_keys=objective_names, value_type=GoodnessOfFitMetrics)

    @classmethod
    def from_json(cls, json_string, objective_names: List[str]):
        json_dict = json.loads(json_string)
        multi_objective_gof_metrics = MultiObjectiveGoodnessOfFitMetrics(objective_names=objective_names)
        for objective_name in objective_names:
            objective_gof_json_string = json_dict[objective_name]
            multi_objective_gof_metrics[objective_name] = GoodnessOfFitMetrics.from_json(json_string=objective_gof_json_string)

        return multi_objective_gof_metrics

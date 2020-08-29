#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from typing import List
from mlos.Optimizers.RegressionModels.RegressionModelFitState import RegressionModelFitState
from mlos.Spaces import Hypergrid


class HomogeneousRandomForestFitState(RegressionModelFitState):
    """ Maintains HomogeneousRandomForest specific fit state in addition to the standard.

    The only difference is, that it also contains a list of RegressionModelFitState objects - one for each
    constituent decision tree.
    """

    def __init__(self, input_space: Hypergrid, output_space: Hypergrid):
        RegressionModelFitState.__init__(self, input_space, output_space)
        self.decision_trees_fit_states: List[RegressionModelFitState] = []

#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from mlos.Optimizers.RegressionModels.MultiObjectiveRegressionModelFitState import MultiObjectiveRegressionModelFitState

class BayesianOptimizerConvergenceState:
    """ Maintains state of the optimizer pertaining to its speed of convergence and quality of surrogate model fit.

    TODO: This is just the first step in writing this class. So at first we will only include the RegressionModelFitState, and then
    TODO: gradually add convergence speed stats, etc.

    """
    def __init__(self, surrogate_model_fit_state: MultiObjectiveRegressionModelFitState):
        self.surrogate_model_fit_state: MultiObjectiveRegressionModelFitState = surrogate_model_fit_state

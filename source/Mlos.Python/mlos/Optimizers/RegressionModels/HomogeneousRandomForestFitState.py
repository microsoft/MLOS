#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from typing import List
import pandas as pd

from mlos.Optimizers.RegressionModels.GoodnessOfFitMetrics import DataSetType
from mlos.Optimizers.RegressionModels.RegressionModelFitState import RegressionModelFitState
from mlos.Spaces import Hypergrid


class HomogeneousRandomForestFitState(RegressionModelFitState):
    """ Maintains HomogeneousRandomForest specific fit state in addition to the standard.

    The only difference is, that it also contains a list of RegressionModelFitState objects - one for each
    constituent decision tree.
    """

    def __init__(self):
        RegressionModelFitState.__init__(self)
        self.decision_trees_fit_states: List[RegressionModelFitState] = []

    def get_goodness_of_fit_dataframe(self, data_set_type: DataSetType, deep=False):
        random_forest_dataframe = RegressionModelFitState.get_goodness_of_fit_dataframe(self, data_set_type=data_set_type)
        if not deep:
            return random_forest_dataframe

        all_dataframes = [random_forest_dataframe]
        for i, tree_fit_state in enumerate(self.decision_trees_fit_states):
            tree_dataframe = tree_fit_state.get_goodness_of_fit_dataframe(data_set_type=data_set_type)
            name_mapping = {
                old_col_name: f"tree_{i}_{old_col_name}" for old_col_name in tree_dataframe.columns.values
            }
            tree_dataframe.rename(columns=name_mapping, inplace=True)
            all_dataframes.append(tree_dataframe)

        combined = pd.concat(all_dataframes, axis=1)
        return combined

#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import numpy as np
import pandas as pd

from typing import List
from mlos.Utils.KeyOrderedDict import KeyOrderedDict
from mlos.Optimizers.RegressionModels.Prediction import Prediction
from mlos.Tracer import trace


class MultiObjectivePrediction(KeyOrderedDict):
    """A container for multiple predictions.

    This is really just an alias to KeyOrderedDict.
    """

    def __init__(self, objective_names: List[str]):
        KeyOrderedDict.__init__(self, ordered_keys=objective_names, value_type=Prediction)

    @trace()
    def create_monte_carlo_samples_df(self, row_idx=0, num_samples=100, max_t_statistic=None):
        predicted_value_col = Prediction.LegalColumnNames.PREDICTED_VALUE.value
        dof_col = Prediction.LegalColumnNames.PREDICTED_VALUE_DEGREES_OF_FREEDOM.value

        monte_carlo_samples_df = pd.DataFrame()

        for objective_name, prediction in self:
            std_dev_column_name = prediction.add_standard_deviation_column()
            prediction_df = prediction.get_dataframe()
            if row_idx not in prediction_df.index:
                return pd.DataFrame(columns=self.ordered_keys, dtype='float')

            config_prediction = prediction_df.loc[row_idx]
            if max_t_statistic is None:
                max_t_statistic = 1000
            monte_carlo_samples_df[objective_name] = np.minimum(max_t_statistic, np.random.standard_t(config_prediction[dof_col], num_samples)) \
                                                     * config_prediction[std_dev_column_name] \
                                                     + config_prediction[predicted_value_col]

        return monte_carlo_samples_df

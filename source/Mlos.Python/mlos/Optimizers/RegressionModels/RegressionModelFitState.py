#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from typing import Dict, List
import pandas as pd
from mlos.Optimizers.RegressionModels.GoodnessOfFitMetrics import GoodnessOfFitMetrics, DataSetType


class RegressionModelFitState:
    """ Maintains the state of the regression model for the benefit of debugging/monitoring.

    The key information we keep here are:

        1. The input and output spaces.
        2. Has the model been fitted.
        3. Goodness of fit metrics (separately on training and testing sets).
        4. ...


    The owning model is responsible for keeping this data up to date and present it on when required.
    """
    def __init__(self):
        self.historical_gof_metrics: Dict[DataSetType, List[GoodnessOfFitMetrics]] = {
            DataSetType.TRAIN: [],
            DataSetType.VALIDATION: [],
            DataSetType.TEST: [],
            DataSetType.TEST_KNOWN_RANDOM: []
        }

    @property
    def has_any_train_gof_metrics(self):
        return len(self.historical_gof_metrics[DataSetType.TRAIN]) > 0

    @property
    def current_train_gof_metrics(self):
        return self.historical_gof_metrics[DataSetType.TRAIN][-1] # TODO: throw a better error than index out of bounds

    def set_gof_metrics(self, data_set_type: DataSetType, gof_metrics: GoodnessOfFitMetrics):
        self.historical_gof_metrics[data_set_type].append(gof_metrics)

    @property
    def train_set_size(self):
        if not self.has_any_train_gof_metrics:
            raise RuntimeError("Trying to retrieve training size of an untrained model.")
        return self.current_train_gof_metrics.observation_count

    # pylint: disable=unused-argument
    def get_goodness_of_fit_dataframe(self, data_set_type: DataSetType = DataSetType.TRAIN, deep=False):
        """ Converts the historical goodness of fit metrics into a data frame.

        :param data_set_type:
        :return:
        """
        gof_metrics_list = self.historical_gof_metrics[data_set_type]
        column_names = GoodnessOfFitMetrics._fields

        values = {col_name: [] for col_name in column_names}

        for gof_record in gof_metrics_list:
            for i, col_name in enumerate(column_names):
                values[col_name].append(gof_record[i])

        del values['data_set_type']
        df = pd.DataFrame(values)
        df = df.drop_duplicates(subset=['last_refit_iteration_number'], keep='last').sort_index()
        return df

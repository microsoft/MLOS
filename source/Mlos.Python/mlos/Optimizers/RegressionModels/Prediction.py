#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from enum import Enum
from typing import List

import numpy as np
import pandas as pd
from scipy.stats import t

class Prediction:
    """ General Prediction class used to capture output from surrogate model .predict() methods

    PredictionSchema defines the known universe of .predict() dataframe columns.  Column names
    will be restricted to the enum values.
    """

    class LegalColumnNames(Enum):
        """ Enum class standardizing the data columns returned by a surrogate model's predict method

        The class defines the "universe" of data returned by a predict() method, but not
        all surrogate models must return all columns.
        """

        # boolean indicating if predict() feature row could be used to make a prediction
        IS_VALID_INPUT = 'is_valid_input'

        # given an instance of the independent variable(s), what's the predicted dependent variable's value
        PREDICTED_VALUE = 'predicted_value'

        """ References:
        https://en.wikipedia.org/wiki/Prediction_interval
        https://stats.stackexchange.com/questions/16493/difference-between-confidence-intervals-and-prediction-intervals
        https://haozhestat.github.io/files/manuscript_RFIntervals_FinalVersion.pdf
        https://www.theoj.org/joss-papers/joss.00124/10.21105.joss.00124.pdf
        """
        PREDICTED_VALUE_VARIANCE = 'predicted_value_variance'
        PREDICTED_VALUE_DEGREES_OF_FREEDOM = 'predicted_value_degrees_of_freedom'
        PREDICTED_VALUE_STANDARD_DEVIATION = 'predicted_value_standard_deviation'

        # https://en.wikipedia.org/wiki/Sample_mean_and_covariance#Sample_mean
        SAMPLE_MEAN = 'sample_mean'

        # https://en.wikipedia.org/wiki/Variance#Sample_variance
        SAMPLE_VARIANCE = 'sample_variance'
        SAMPLE_SIZE = 'sample_size'

        DEGREES_OF_FREEDOM = 'degrees_of_freedom'

    @classmethod
    def create_prediction_from_dataframe(cls, objective_name: str, dataframe: pd.DataFrame):
        assert objective_name is not None
        predictor_outputs = [
            Prediction.LegalColumnNames(column_name)
            for column_name
            in dataframe.columns.values
        ]
        return Prediction(
            objective_name=objective_name,
            predictor_outputs=predictor_outputs,
            dataframe=dataframe
        )

    def __init__(
            self,
            objective_name: str,
            predictor_outputs: List[LegalColumnNames],
            dataframe_index: pd.Index = None,
            dataframe: pd.DataFrame = None,
            num_head_rows_to_print: int = 1,
            allow_extra_columns: bool = False
    ):
        self.objective_name = objective_name
        self.num_head_rows_to_print = num_head_rows_to_print

        # validate passed args
        for output_enum in predictor_outputs:
            assert output_enum in set(column_name for column_name in Prediction.LegalColumnNames), \
                f'PredictionSchema Error: Passed PredictionSchema enum "{output_enum}" not in Prediction.PredictionSchema'
        self.predictor_outputs = predictor_outputs

        # expect dataframe column names to be values from Enum above
        self.expected_column_names = [output_enum.value for output_enum in self.predictor_outputs]
        self.allow_extra_columns = allow_extra_columns

        self._dataframe = pd.DataFrame(columns=self.expected_column_names, index=dataframe_index)
        if dataframe is not None:
            self.set_dataframe(dataframe)

    def set_dataframe(self, dataframe: pd.DataFrame):
        self.validate_dataframe(dataframe)
        if self._dataframe.index.empty or (len(self._dataframe.index) == len(dataframe.index) and self._dataframe.index.equals(dataframe.index)):
            self._dataframe = dataframe
        else:
            self._dataframe.loc[dataframe.index, self.expected_column_names] = dataframe[self.expected_column_names]

    def validate_dataframe(self, dataframe: pd.DataFrame):

        if not self.allow_extra_columns:
            # validate passed columns exist in LegalColumnNames enum
            for column_name in dataframe.columns.values:
                assert column_name in self.expected_column_names, \
                    f'PredictionSchema Error: Failed to find "{column_name}" in Prediction.PredictionSchema class'

        # validate all declared columns (in model's SCHEMA) are present in the dataframe
        for expected_column_name in self.expected_column_names:
            assert expected_column_name in dataframe.columns.values, \
                f'PredictionSchema Error: Failed to find expected column name "{expected_column_name}" in passed dataframe'

        mean_variance_col = self.LegalColumnNames.PREDICTED_VALUE_VARIANCE.value
        sample_variance_col = self.LegalColumnNames.SAMPLE_VARIANCE.value

        if mean_variance_col in self.expected_column_names:
            if dataframe[mean_variance_col].notnull().any():
                assert (dataframe[dataframe[mean_variance_col].notnull()][mean_variance_col] >= 0).all()

        if sample_variance_col in self.expected_column_names:
            if dataframe[sample_variance_col].notnull().any():
                assert (dataframe[dataframe[sample_variance_col].notnull()][sample_variance_col] >= 0).all()


    @classmethod
    def get_enum_by_column_name(cls, column_name):
        return Prediction.LegalColumnNames(column_name)

    def get_dataframe(self):
        return self._dataframe

    @classmethod
    def dataframe_from_json(cls, json_string):
        return pd.read_json(json_string, orient='index')

    def dataframe_to_json(self):
        return self.get_dataframe().to_json(orient='index', double_precision=15)

    def __repr__(self):
        rows_as_dict = self._dataframe.head(self.num_head_rows_to_print).to_dict(orient='records')
        return 'objective_name: {name}, dataframe.head({num_rows}): {rows_as_dict}'.format(
            name=self.objective_name,
            num_rows=self.num_head_rows_to_print,
            rows_as_dict=rows_as_dict
        )

    def add_invalid_rows_at_missing_indices(self, desired_index):
        assert self._dataframe.index.intersection(desired_index).equals(self._dataframe.index),\
            "Desired index must be a superset of the existing index."
        invalid_predictions_index = desired_index.difference(self._dataframe.index)
        self.add_invalid_prediction_rows(invalid_predictions_index)

    def add_invalid_prediction_rows(self, invalid_predictions_index):
        """ Inserts rows with LegalColumnNames.IS_VALID_INPUT column set to False, and all other columns set to NaN at specified index.

        This is useful if a model can only produce valid predictions for a subset of rows, but the caller expects a dataframe
        with index matching the index of the features dataframe.

        :param invalid_predictions_index:
        :return:
        """
        if not invalid_predictions_index.empty:
            assert invalid_predictions_index.intersection(self._dataframe.index).empty, "Valid and invalid indices cannot overlap."
            if self.LegalColumnNames.IS_VALID_INPUT.value not in self.expected_column_names:
                self.expected_column_names.append(self.LegalColumnNames.IS_VALID_INPUT.value)
            invalid_predictions_df = pd.DataFrame(columns=self.expected_column_names, index=invalid_predictions_index)
            invalid_predictions_df[self.LegalColumnNames.IS_VALID_INPUT.value] = False
            all_predictions_df = pd.concat([self._dataframe, invalid_predictions_df])
            all_predictions_df.sort_index(inplace=True)
            self.validate_dataframe(all_predictions_df)
            self._dataframe = all_predictions_df

    def add_standard_deviation_column(self) -> str:
        """Appends a standard deviation column to the prediction dataframe and returns the new column's name.

        This is a convenience function - many users of the Prediction object need to know the standard deviation rather than
        variance so it makes sense to add it as a feature here.

        :return:
            TODO: format return type properly
            new column name
        """
        std_dev_col_name = self.LegalColumnNames.PREDICTED_VALUE_STANDARD_DEVIATION.name
        variance_col_name = self.LegalColumnNames.PREDICTED_VALUE_VARIANCE.value
        self._dataframe[std_dev_col_name] = np.sqrt(self._dataframe[variance_col_name])
        return std_dev_col_name


    def add_t_values_column(self, alpha: float) -> str:
        """Appends a t-values column for a given alpha to the prediction dataframe and returns the new column's name.

        :param alpha:
        :return:
        """
        assert 0.0 < alpha < 1.0
        t_values_column_name = f"t_value_{(1-alpha)*100:.1f}".replace(".", "_point_")
        self._dataframe[t_values_column_name] = t.ppf(1 - alpha / 2.0, self._dataframe[self.LegalColumnNames.PREDICTED_VALUE_DEGREES_OF_FREEDOM])
        return t_values_column_name

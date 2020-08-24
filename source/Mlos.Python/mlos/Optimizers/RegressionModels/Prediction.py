#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from enum import Enum
from typing import List
import json
import pandas as pd

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

        # https://en.wikipedia.org/wiki/Sample_mean_and_covariance#Sample_mean
        SAMPLE_MEAN = 'sample_mean'

        # https://en.wikipedia.org/wiki/Variance#Sample_variance
        SAMPLE_VARIANCE = 'sample_variance'
        SAMPLE_SIZE = 'sample_size'

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
            dataframe: pd.DataFrame = None,
            num_head_rows_to_print: int = 1
    ):
        self.objective_name = objective_name
        self.num_head_rows_to_print = num_head_rows_to_print

        # validate passed args
        for output_enum in predictor_outputs:
            assert output_enum in Prediction.LegalColumnNames, \
                f'PredictionSchema Error: Passed PredictionSchema enum "{output_enum}" not in Prediction.PredictionSchema'
        self.predictor_outputs = predictor_outputs

        # expect dataframe column names to be values from Enum above
        self.expected_column_names = [output_enum.value for output_enum in self.predictor_outputs]

        self._dataframe = None
        if dataframe is None:
            self._dataframe = pd.DataFrame(columns=self.expected_column_names)
        else:
            self.set_dataframe(dataframe)

    def set_dataframe(self, dataframe: pd.DataFrame):
        # validate passed columns exist in LegalColumnNames enum
        for column_name in dataframe.columns.values:
            assert column_name in self.expected_column_names, \
                f'PredictionSchema Error: Failed to find "{column_name}" in Prediction.PredictionSchema class'

        # validate all declared columns (in model's SCHEMA) are present in the dataframe
        for expected_column_name in self.expected_column_names:
            assert expected_column_name in dataframe.columns.values, \
                f'PredictionSchema Error: Failed to find expected column name "{expected_column_name}" in passed dataframe'

        self._dataframe = dataframe

    @classmethod
    def get_enum_by_column_name(cls, column_name):
        return Prediction.LegalColumnNames(column_name)

    def get_dataframe(self):
        return self._dataframe

    @classmethod
    def dataframe_from_json(cls, json_string):
        return pd.DataFrame.from_dict(json.loads(json_string))

    def dataframe_to_json(self):
        return json.dumps(self.get_dataframe().to_dict(orient='list'))

    def __str__(self):
        rows_as_dict = self._dataframe.head(self.num_head_rows_to_print).to_dict(orient='records')
        return 'objective_name: {name}, dataframe.head({num_rows}): {rows_as_dict}'.format(
            name=self.objective_name,
            num_rows=self.num_head_rows_to_print,
            rows_as_dict=rows_as_dict
        )

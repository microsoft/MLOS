#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from enum import Enum
import json
from typing import NamedTuple


class DataSetType(Enum):
    TRAIN = 0
    VALIDATION = 1
    TEST = 2
    # Observations known to be based on i.i.d random sampling. These observations are the result of the
    # Experiment Designer suggesting a random configuration.
    #
    TEST_KNOWN_RANDOM = 3


class GoodnessOfFitMetrics(NamedTuple):
    """ GOF metrics for a given model for given data.

    Using this as a start:
        https://medium.com/microsoftazure/how-to-better-evaluate-the-goodness-of-fit-of-regressions-990dbf1c0091
    """

    last_refit_iteration_number: int
    observation_count: int = 0
    prediction_count: int = 0
    data_set_type: DataSetType = DataSetType.TRAIN
    mean_absolute_error: float = None
    root_mean_squared_error: float = None
    relative_absolute_error: float = None
    relative_squared_error: float = None
    coefficient_of_determination: float = None
    # adjusted_coefficient_of_determination: float = None
    prediction_90_ci_hit_rate: float = None
    # prediction_95_ci_hit_rate: float = None
    # prediction_99_ci_hit_rate: float = None
    sample_90_ci_hit_rate: float = None
    # sample_95_ci_hit_rate: float = None
    # sample_99_ci_hit_rate: float = None

    def to_json(self):
        return json.dumps({
            "last_refit_iteration_number": self.last_refit_iteration_number,
            "observation_count": self.observation_count,
            "prediction_count": self.prediction_count,
            "data_set_type": self.data_set_type.value,
            "mean_absolute_error": self.mean_absolute_error,
            "root_mean_squared_error": self.root_mean_squared_error,
            "relative_absolute_error": self.relative_absolute_error,
            "relative_squared_error": self.relative_squared_error,
            "coefficient_of_determination": self.coefficient_of_determination,
            "prediction_90_ci_hit_rate": self.prediction_90_ci_hit_rate,
            "sample_90_ci_hit_rate": self.sample_90_ci_hit_rate
        })

    @classmethod
    def from_json(cls, json_string):
        json_dict = json.loads(json_string)
        return GoodnessOfFitMetrics(
            last_refit_iteration_number=json_dict["last_refit_iteration_number"],
            observation_count=json_dict["observation_count"],
            prediction_count=json_dict["prediction_count"],
            data_set_type=json_dict["data_set_type"],
            mean_absolute_error=json_dict["mean_absolute_error"],
            root_mean_squared_error=json_dict["root_mean_squared_error"],
            relative_absolute_error=json_dict["relative_absolute_error"],
            relative_squared_error=json_dict["relative_squared_error"],
            coefficient_of_determination=json_dict["coefficient_of_determination"],
            prediction_90_ci_hit_rate=json_dict["prediction_90_ci_hit_rate"],
            sample_90_ci_hit_rate=json_dict["sample_90_ci_hit_rate"]
        )

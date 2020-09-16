#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from enum import Enum
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

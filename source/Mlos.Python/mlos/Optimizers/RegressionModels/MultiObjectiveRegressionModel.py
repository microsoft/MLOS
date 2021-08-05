#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from abc import ABC, abstractmethod

import pandas as pd

from mlos.Spaces import Hypergrid, Point
from mlos.Optimizers.RegressionModels.GoodnessOfFitMetrics import DataSetType
from mlos.Optimizers.RegressionModels.MultiObjectiveGoodnessOfFitMetrics import MultiObjectiveGoodnessOfFitMetrics
from mlos.Optimizers.RegressionModels.MultiObjectivePrediction import MultiObjectivePrediction
from mlos.Optimizers.RegressionModels.MultiObjectiveRegressionModelFitState import MultiObjectiveRegressionModelFitState


class MultiObjectiveRegressionModel(ABC):
    """A base class for all multi-objective regression models to implement."""


    def __init__(
            self,
            model_type: type,
            model_config: Point,
            input_space: Hypergrid,
            output_space: Hypergrid
    ):
        self.model_type = model_type
        self.model_config = model_config
        self.input_space = input_space
        self.output_space = output_space

        self.input_dimension_names = self.input_space.dimension_names
        self.output_dimension_names = self.output_space.dimension_names

    @property
    @abstractmethod
    def fit_state(self) -> MultiObjectiveRegressionModelFitState:
        raise NotImplementedError

    @property
    @abstractmethod
    def trained(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def fit(self, features_df: pd.DataFrame, targets_df: pd.DataFrame, iteration_number: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def predict(self, features_df: pd.DataFrame, include_only_valid_rows: bool = True) -> MultiObjectivePrediction:
        raise NotImplementedError

    @abstractmethod
    def compute_goodness_of_fit(self, features_df: pd.DataFrame, targets_df: pd.DataFrame, data_set_type: DataSetType) -> MultiObjectiveGoodnessOfFitMetrics:
        raise NotImplementedError

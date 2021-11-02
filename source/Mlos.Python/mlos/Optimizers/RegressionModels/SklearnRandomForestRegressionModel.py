#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import logging
from typing import List
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GridSearchCV

from mlos.Logger import create_logger
from mlos.Optimizers.RegressionModels.RegressionModel import RegressionModel
from mlos.Optimizers.RegressionModels.Prediction import Prediction
from mlos.Optimizers.RegressionModels.SklearnRandomForestRegressionModelConfig import SklearnRandomForestRegressionModelConfig
from mlos.Spaces import SimpleHypergrid, Hypergrid, Point
from mlos.Spaces.Dimensions.ContinuousDimension import ContinuousDimension

from mlos.Spaces.HypergridAdapters.CategoricalToOneHotEncodedHypergridAdapter import CategoricalToOneHotEncodedHypergridAdapter


class SklearnRandomForestRegressionModel(RegressionModel):
    """Thin wrapper for the scikit-learn RandomForestRegressor.

    This model natively support multi-output regression.
    """

    _PREDICTOR_OUTPUT_COLUMNS = [
        Prediction.LegalColumnNames.IS_VALID_INPUT,
        Prediction.LegalColumnNames.PREDICTED_VALUE,
        Prediction.LegalColumnNames.PREDICTED_VALUE_VARIANCE,
        Prediction.LegalColumnNames.PREDICTED_VALUE_DEGREES_OF_FREEDOM
    ]

    def __init__(
            self,
            model_config: Point,
            input_space: Hypergrid,
            output_space: Hypergrid,
            logger: logging.Logger = None
    ):
        if logger is None:
            logger = create_logger("SklearnRandomForestRegressionModel")
        self.logger = logger
        assert model_config in SklearnRandomForestRegressionModelConfig.CONFIG_SPACE
        RegressionModel.__init__(
            self,
            model_type=type(self),
            model_config=model_config,
            input_space=input_space,
            output_space=output_space
        )

        self.model_config = model_config

        # one hot encode categorical input dimensions
        self.one_hot_encoder_adapter = CategoricalToOneHotEncodedHypergridAdapter(
            adaptee=self.polynomial_features_adapter,
            merge_all_categorical_dimensions=True,
            drop='first'
        )

        self.input_dimension_names = [dimension.name for dimension in self.input_space.dimensions]
        self._projected_input_dimension_names = [dimension.name for dimension in self.one_hot_encoder_adapter.dimensions]
        self.continuous_dimension_names = [dimension.name for dimension in self.one_hot_encoder_adapter.target.dimensions
                                           if isinstance(dimension, ContinuousDimension)]
        self.output_dimension_names = [dimension.name for dimension in self.output_space.dimensions]

        self.random_forest_regressor_ = None

        self.fit_X_ = None

        self.trained = False
        self.last_refit_iteration_number = None

    def fit(
            self,
            feature_values_pandas_frame: pd.DataFrame,
            target_values_pandas_frame: pd.DataFrame,
    ):
        """ Fits the RegressionEnhancedRandomForest
        :param feature_values_pandas_frame:
        :param target_values_pandas_frame:
        :return:
        """
        features_df = self.one_hot_encoder_adapter.project_dataframe(feature_values_pandas_frame, in_place=False)

        model_config = self.model_config.sklearn_random_forest_regression_model_config

        self.random_forest_regressor_ = RandomForestRegressor(
            n_estimators=model_config.n_estimators,
            criterion=model_config.criterion,
            max_depth=model_config.max_depth if model_config.max_depth > 0 else None,
            min_samples_split=model_config.min_samples_split,
            min_samples_leaf=model_config.min_samples_leaf,
            min_weight_fraction_leaf=model_config.min_weight_fraction_leaf,
            max_features=model_config.max_features,
            max_leaf_nodes=model_config.max_leaf_nodes if model_config.max_leaf_nodes > 0 else None,
            min_impurity_decrease=model_config.min_impurity_decrease,
            bootstrap=model_config.bootstrap,
            oob_score=model_config.oob_score,
            n_jobs=model_config.n_jobs,
            warm_start=model_config.warm_start,
            ccp_alpha=model_config.ccp_alpha,
            max_samples=model_config.max_samples if model_config.max_samples > 0 else None
        )

        self.random_forest_regressor_.fit(
            features_df,
            target_values_pandas_frame)

        return self


    def predict(
            self,
            feature_values_pandas_frame: pd.DataFrame,
            include_only_valid_rows: bool = True
    ) -> Prediction:

        # Prediction dataframe column shortcuts
        is_valid_input_col = Prediction.LegalColumnNames.IS_VALID_INPUT.value
        predicted_value_col = Prediction.LegalColumnNames.PREDICTED_VALUE.value
        predicted_value_var_col = Prediction.LegalColumnNames.PREDICTED_VALUE_VARIANCE.value
        dof_col = Prediction.LegalColumnNames.PREDICTED_VALUE_DEGREES_OF_FREEDOM.value

        valid_rows_index = None
        if self.trained:
            feature_values_pandas_frame = self.input_space.filter_out_invalid_rows(original_dataframe=feature_values_pandas_frame, exclude_extra_columns=False)

            features_df = self.one_hot_encoder_adapter.project_dataframe(feature_values_pandas_frame, in_place=False)
            valid_rows_index = feature_values_pandas_frame.index

        # initialize return predictions
        predictions = Prediction(
            objective_name=self.target_dimension_names[0],
            predictor_outputs=self._PREDICTOR_OUTPUT_COLUMNS,
            dataframe_index=valid_rows_index
        )
        prediction_dataframe = predictions.get_dataframe()

        if valid_rows_index is not None and not valid_rows_index.empty:
            prediction_dataframe[is_valid_input_col] = True

            predictions = self.random_forest_regressor_.predict(features_df)
            prediction_dataframe[predicted_value_col] = predictions
            # FIXME
            # prediction_dataframe[dof_col] = self.dof_

            # compute variance needed for prediction interval
            # FIXME
            # var_list = []
            # prediction_dataframe[predicted_value_var_col] = var_list
        predictions.validate_dataframe(prediction_dataframe)

        if not include_only_valid_rows:
            predictions.add_invalid_rows_at_missing_indices(desired_index=feature_values_pandas_frame.index)

        return predictions
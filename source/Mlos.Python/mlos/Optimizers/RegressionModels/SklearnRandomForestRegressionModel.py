#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import logging
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestRegressor

from mlos.Logger import create_logger
from mlos.Optimizers.RegressionModels.RegressionModel import RegressionModel
from mlos.Optimizers.RegressionModels.Prediction import Prediction
from mlos.Optimizers.RegressionModels.SklearnRandomForestRegressionModelConfig import SklearnRandomForestRegressionModelConfig
from mlos.Spaces import Hypergrid, Point
from mlos.Spaces.Dimensions.ContinuousDimension import ContinuousDimension

from mlos.Spaces.HypergridAdapters.CategoricalToOneHotEncodedHypergridAdapter import CategoricalToOneHotEncodedHypergridAdapter


# taken form scikit-optimize. BSD licensed by the scikit-optimize developers
# https://github.com/scikit-optimize/scikit-optimize/blob/master/skopt/learning/forest.py

def _return_std(X, trees, predictions, min_variance):
    """
    Returns `std(Y | X)`.
    Can be calculated by E[Var(Y | Tree)] + Var(E[Y | Tree]) where
    P(Tree) is `1 / len(trees)`.
    Parameters
    ----------
    X : array-like, shape=(n_samples, n_features)
        Input data.
    trees : list, shape=(n_estimators,)
        List of fit sklearn trees as obtained from the ``estimators_``
        attribute of a fit RandomForestRegressor or ExtraTreesRegressor.
    predictions : array-like, shape=(n_samples,)
        Prediction of each data point as returned by RandomForestRegressor
        or ExtraTreesRegressor.
    Returns
    -------
    std : array-like, shape=(n_samples,)
        Standard deviation of `y` at `X`. If criterion
        is set to "mse", then `std[i] ~= std(y | X[i])`.
    """
    # This derives std(y | x) as described in 4.3.2 of arXiv:1211.0906
    std = np.zeros(len(X))

    for tree in trees:
        var_tree = tree.tree_.impurity[tree.apply(X)]

        # This rounding off is done in accordance with the
        # adjustment done in section 4.3.3
        # of http://arxiv.org/pdf/1211.0906v2.pdf to account
        # for cases such as leaves with 1 sample in which there
        # is zero variance.
        var_tree[var_tree < min_variance] = min_variance
        mean_tree = tree.predict(X)
        std += var_tree + mean_tree ** 2

    std /= len(trees)
    std -= predictions ** 2.0
    std[std < 0.0] = 0.0
    std = std ** 0.5
    return std

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

        if model_config.oob_score:
            model_config.bootstrap = True

        if len(output_space.dimensions) > 1:
            ValueError("Multi-output regression is not yet supported. ")

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
            adaptee=self.input_space,
            merge_all_categorical_dimensions=False)

        self.input_dimension_names = [dimension.name for dimension in self.input_space.dimensions]
        self._projected_input_dimension_names = [dimension.name for dimension in self.one_hot_encoder_adapter.dimensions]
        self.continuous_dimension_names = [dimension.name for dimension in self.one_hot_encoder_adapter.target.dimensions
                                           if isinstance(dimension, ContinuousDimension)]
        self.output_dimension_names = [dimension.name for dimension in self.output_space.dimensions]

        self.random_forest_regressor_ = None

        self.fit_X_ = None

        self._trained = False
        self.last_refit_iteration_number = None


    @property
    def trained(self):
        return self._trained


    def fit(
            self,
            features_df: pd.DataFrame,
            targets_df: pd.DataFrame,
            iteration_number: int
    ):
        """ Fits the RegressionEnhancedRandomForest
        :param feature_values_pandas_frame:
        :param target_values_pandas_frame:
        :return:
        """
        features_df_ohe = self.one_hot_encoder_adapter.project_dataframe(features_df, in_place=False)

        model_config = self.model_config

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
            features_df_ohe,
            targets_df)

        self._trained = True
        return self


    def predict(
            self,
            features_df: pd.DataFrame,
            include_only_valid_rows: bool = True
    ) -> Prediction:

        # Prediction dataframe column shortcuts
        is_valid_input_col = Prediction.LegalColumnNames.IS_VALID_INPUT.value
        predicted_value_col = Prediction.LegalColumnNames.PREDICTED_VALUE.value
        predicted_value_var_col = Prediction.LegalColumnNames.PREDICTED_VALUE_VARIANCE.value

        valid_rows_index = None
        if self.trained:
            feature_values_pandas_frame = self.input_space.filter_out_invalid_rows(original_dataframe=features_df, exclude_extra_columns=False)

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

            predictions_array = self.random_forest_regressor_.predict(features_df)

            predicted_std = _return_std(features_df, self.random_forest_regressor_.estimators_, predictions_array, min_variance=0.01)
            prediction_dataframe[predicted_value_col] = predictions_array

            prediction_dataframe[predicted_value_var_col] = predicted_std ** 2
        predictions.validate_dataframe(prediction_dataframe)

        if not include_only_valid_rows:
            predictions.add_invalid_rows_at_missing_indices(desired_index=feature_values_pandas_frame.index)

        return [predictions]
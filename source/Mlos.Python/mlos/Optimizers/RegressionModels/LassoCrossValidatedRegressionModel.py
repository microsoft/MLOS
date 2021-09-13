#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import logging
import numpy as np
from pandas import DataFrame
from sklearn.linear_model import LassoCV

from mlos.Logger import create_logger
from mlos.Optimizers.RegressionModels.Prediction import Prediction
from mlos.Optimizers.RegressionModels.RegressionModel import RegressionModel
from mlos.Optimizers.RegressionModels.LassoCrossValidatedConfigStore import lasso_cross_validated_config_store
from mlos.Spaces.HypergridAdapters.CategoricalToOneHotEncodedHypergridAdapter import CategoricalToOneHotEncodedHypergridAdapter
from mlos.Spaces.Dimensions.ContinuousDimension import ContinuousDimension
from mlos.Spaces import Hypergrid, Point
from mlos.Tracer import trace


class LassoCrossValidatedRegressionModel(RegressionModel):
    """ Wraps sklearn's linear_model.LassoCV regression model.
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
            logger = create_logger("LassoRegressionModel")
        self.logger = logger

        assert model_config in lasso_cross_validated_config_store.parameter_space
        RegressionModel.__init__(
            self,
            model_type=type(self),
            model_config=model_config,
            input_space=input_space,
            output_space=output_space
        )

        # setup adapters to accommodate categorical dimensions
        # one hot encode categorical input dimensions
        self.one_hot_encoder_adapter = CategoricalToOneHotEncodedHypergridAdapter(
            adaptee=input_space,
            merge_all_categorical_dimensions=True,
            drop='first'
        )
        self.input_dimension_names = self.input_space.dimension_names

        self._projected_input_dimension_names = [dimension.name for dimension in self.one_hot_encoder_adapter.dimensions]
        self.continuous_dimension_names = [dimension.name for dimension in self.one_hot_encoder_adapter.target.dimensions
                                           if isinstance(dimension, ContinuousDimension)]
        self.target_dimension_names = [dimension.name for dimension in self.output_space.dimensions]
        self.logger.debug(f"Input dimensions: {str(self._projected_input_dimension_names)}; Target dimensions: {str(self.target_dimension_names)}.")

        assert len(self.target_dimension_names) == 1, "For now (and perhaps forever) we only support single target per Lasso model."

        self.lasso_model_kwargs = {
            'eps': self.model_config.eps,
            'n_alphas': self.model_config.num_alphas,
            'alphas': None,
            'fit_intercept': self.model_config.fit_intercept,
            'normalize': self.model_config.normalize,
            'precompute': self.model_config.precompute,
            'max_iter': self.model_config.max_iter,
            'tol': self.model_config.tol,
            'copy_X': self.model_config.copy_x,
            'cv': self.model_config.num_cross_validations,
            'verbose': self.model_config.verbose,
            'n_jobs': self.model_config.num_jobs,
            'positive': self.model_config.positive,
            'random_state': None,
            'selection': self.model_config.selection
        }
        self._regressor = LassoCV(**self.lasso_model_kwargs)
        self._trained: bool = False
        self.last_refit_iteration_number = None

        self.categorical_zero_cols_idx_to_delete_ = None
        self.dof_ = 0
        self.partial_hat_matrix_ = 0
        self.regressor_standard_error_ = 0

        # When LassoCV is used as part of RERF, it cannot reasonably compute the upper and lower bounds on its input space dimensions,
        # as they are a polynomial combination of inputs to RERF. Thus, it approximates them with the empirical min and max.
        # These approximations are biased: the lower bound is too large, the upper bound is too small.
        # Consequently, during scoring, LassoCV is likely to see input outside of these bounds, but we still want
        # LassoCV to produce predictions for those points. So we introduce a little hack: whenever LassoCV is instantiated as part of RERF,
        # it should skip input filtering on predict. This field, controls this behavior.
        self.skip_input_filtering_on_predict = False


    @property
    def trained(self):
        return self._trained

    @property
    def num_observations_used_to_fit(self):
        return self.last_refit_iteration_number

    @property
    def coef_(self):
        if self.trained:
            return self._regressor.coef_
        return None

    @property
    def intercept_(self):
        if self.trained:
            return self._regressor.intercept_
        return None

    # TODO : the condition number of the p hat matrix is likely the ultimate factor in knowing if fit should be done
    def should_fit(self, num_samples):
        """ Returns true if the model should be fitted.

        This model should be fitted under the following conditions:
        1) It has not been fitted yet and num_samples is larger than min_samples_to_fit
        2) The model has been fitted and the number of new samples is larger than n_new_samples_before_refit

        :param num_samples:
        :return:
        """
        num_input_dims = len(self._projected_input_dimension_names)
        model_config = self.model_config
        if not self.trained:
            return num_samples > model_config.min_num_samples_per_input_dimension_to_fit * num_input_dims
        num_new_samples = num_samples - self.num_observations_used_to_fit
        return num_new_samples >= model_config.num_new_samples_per_input_dimension_before_refit * num_input_dims

    @trace()
    def fit(self, feature_values_pandas_frame, target_values_pandas_frame, iteration_number):
        self.logger.debug(f"Fitting a {self.__class__.__name__} with {len(feature_values_pandas_frame.index)} observations.")

        # Let's get the numpy arrays out of the panda frames
        x_df = self.one_hot_encoder_adapter.project_dataframe(feature_values_pandas_frame, in_place=False)
        y = target_values_pandas_frame[self.target_dimension_names].to_numpy()
        design_matrix = self._transform_x(x_df)

        # ensure num_cross_validations < num_samples; and reinstantiate LassoCV regressor
        if design_matrix.shape[0] < self.model_config.num_cross_validations:
            self.lasso_model_kwargs['cv'] = design_matrix.shape[0] - 1
            self._regressor = LassoCV(**self.lasso_model_kwargs)

        self._regressor.fit(design_matrix, y)
        self._trained = True
        self.last_refit_iteration_number = iteration_number

        # retain inverse(x.T * x) to use for confidence intervals on predicted values
        condition_number = np.linalg.cond(design_matrix)
        self.logger.info(
            f'LassoCV: design_matrix condition number: {condition_number}'
        )
        if condition_number > 10.0 ** 4:
            # add small noise to x to remove singularity,
            #  expect prediction confidence to be reduced (wider intervals) by doing this
            self.logger.info(
                f"Adding noise to design matrix used for prediction confidence due to condition number {condition_number} > 10**4."
            )
            design_matrix += np.random.normal(0, 10.0**-2, size=design_matrix.shape)
            condition_number = np.linalg.cond(design_matrix)
            self.logger.info(
                f"Resulting condition number {condition_number}."
            )
        x_transpose_times_x = np.matmul(design_matrix.T, design_matrix)
        self.partial_hat_matrix_ = np.linalg.inv(x_transpose_times_x)

        # retain standard error from base model (used for prediction confidence intervals)
        predicted_y = self._regressor.predict(design_matrix)
        y_residuals = y - predicted_y
        residual_sum_of_squares = np.sum(y_residuals ** 2)
        self.dof_ = design_matrix.shape[0] - (len(self._regressor.coef_) + 1)  # +1 for intercept
        self.regressor_standard_error_ = residual_sum_of_squares / float(self.dof_)

    @trace()
    def predict(self, feature_values_pandas_frame, include_only_valid_rows=True):
        self.logger.debug(f"Creating predictions for {len(feature_values_pandas_frame.index)} samples.")

        # Prediction dataframe column shortcuts
        is_valid_input_col = Prediction.LegalColumnNames.IS_VALID_INPUT.value
        predicted_value_col = Prediction.LegalColumnNames.PREDICTED_VALUE.value
        predicted_value_var_col = Prediction.LegalColumnNames.PREDICTED_VALUE_VARIANCE.value
        dof_col = Prediction.LegalColumnNames.PREDICTED_VALUE_DEGREES_OF_FREEDOM.value

        valid_rows_index = None
        features_df = None
        if self.trained:
            if not self.skip_input_filtering_on_predict:
                feature_values_pandas_frame = self.input_space.filter_out_invalid_rows(
                    original_dataframe=feature_values_pandas_frame,
                    exclude_extra_columns=False
                )
            features_df = self.one_hot_encoder_adapter.project_dataframe(feature_values_pandas_frame, in_place=False)
            valid_rows_index = features_df.index

        predictions = Prediction(
            objective_name=self.target_dimension_names[0],
            predictor_outputs=self._PREDICTOR_OUTPUT_COLUMNS,
            dataframe_index=valid_rows_index
        )
        prediction_dataframe = predictions.get_dataframe()

        if valid_rows_index is not None and not valid_rows_index.empty:
            prediction_dataframe[is_valid_input_col] = True

            # if len(self.one_hot_encoder_adapter.get_one_hot_encoded_column_names()) > 0:
            #     design_matrix = self._create_one_hot_encoded_design_matrix(features_df)
            # else:
            #     design_matrix = features_df.to_numpy()
            design_matrix = self._transform_x(features_df)
            prediction_dataframe[predicted_value_col] = self._regressor.predict(design_matrix)

            # compute variance needed for prediction interval
            prediction_variances = []
            for xi in design_matrix:
                leverage_x = np.matmul(np.matmul(xi.T, self.partial_hat_matrix_), xi)
                prediction_var = self.regressor_standard_error_ * (1.0 + leverage_x)
                prediction_variances.append(prediction_var if prediction_var > 0 else 0)

            prediction_dataframe[predicted_value_var_col] = prediction_variances
            prediction_dataframe[dof_col] = self.dof_

        predictions.validate_dataframe(prediction_dataframe)
        if not include_only_valid_rows:
            predictions.add_invalid_rows_at_missing_indices(desired_index=feature_values_pandas_frame.index)
        return predictions

    def _transform_x(self, x_df: DataFrame):
        # confirm feature_values_pandas_frame contains all expected columns
        #  if any are missing, impute NaN values
        missing_column_names = set.difference(set(self._projected_input_dimension_names), set(x_df.columns.values))
        for missing_column_name in missing_column_names:
            x_df[missing_column_name] = np.NaN

        # impute 0s for NaNs (NaNs can come from hierarchical hypergrids)
        x_df.fillna(value=0, inplace=True)

        # construct traditional design matrix when fitting with one hot encoded categorical dimensions
        if len(self.one_hot_encoder_adapter.get_one_hot_encoded_column_names()) > 0:
            design_matrix = self._create_one_hot_encoded_design_matrix(x_df)
        else:
            design_matrix = x_df.to_numpy()
        return design_matrix

    def _create_one_hot_encoded_design_matrix(self, x: DataFrame) -> np.ndarray:
        assert len(self.one_hot_encoder_adapter.get_one_hot_encoded_column_names()) > 0

        # use the following to create one hot encoding columns prior to constructing fit_x and powers_ table
        num_continuous_features = len(self.continuous_dimension_names)
        continuous_features_x = x[self.continuous_dimension_names]

        dummy_var_cols = self.one_hot_encoder_adapter.get_one_hot_encoded_column_names()
        num_dummy_vars = len(dummy_var_cols)

        # initialize the design matrix
        fit_x = np.zeros((x.shape[0], num_continuous_features * (num_dummy_vars + 1)))

        # add polynomial features weighted by oneHotEncoded columns
        # add polynomial for 000...000 encoding
        fit_x[:, 0:num_continuous_features] = continuous_features_x.copy().to_numpy()

        # add ohe * polynomial terms for non-000...000 encodings
        last_col_filled = num_continuous_features
        for ohe_col_name in dummy_var_cols:
            fit_x[:, last_col_filled:last_col_filled + num_continuous_features] = \
                x[ohe_col_name].to_numpy().reshape(-1, 1) * continuous_features_x.copy().to_numpy()
            last_col_filled += num_continuous_features

        # check for zero columns (expected with hierarchical feature hypergrids containing NaNs for some features)
        #  this should eliminate singular design matrix errors from lasso/ridge regressions
        if self.categorical_zero_cols_idx_to_delete_ is None:
            self.categorical_zero_cols_idx_to_delete_ = np.argwhere(np.all(fit_x[..., :] == 0, axis=0))
        # remembered from .fit() if not set above
        zero_cols_idx = self.categorical_zero_cols_idx_to_delete_
        if zero_cols_idx.any():
            fit_x = np.delete(fit_x, zero_cols_idx, axis=1)

        return fit_x

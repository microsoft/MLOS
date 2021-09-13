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
from mlos.Optimizers.RegressionModels.LassoCrossValidatedRegressionModel import LassoCrossValidatedRegressionModel
from mlos.Optimizers.RegressionModels.RegressionEnhancedRandomForestConfigStore import regression_enhanced_random_forest_config_store
from mlos.Spaces import SimpleHypergrid, Hypergrid, Point
from mlos.Spaces.Dimensions.ContinuousDimension import ContinuousDimension

from mlos.Spaces.HypergridAdapters.CategoricalToOneHotEncodedHypergridAdapter import CategoricalToOneHotEncodedHypergridAdapter
from mlos.Spaces.HypergridAdapters.ContinuousToPolynomialBasisHypergridAdapter import ContinuousToPolynomialBasisHypergridAdapter
from mlos.Tracer import trace


class RegressionEnhancedRandomForestRegressionModel(RegressionModel):
    """ Regression-Enhanced RandomForest Regression model
    See https://arxiv.org/pdf/1904.10416.pdf for inspiration.
    See following PRs for exploration notes/observations:
    1. https://msdata.visualstudio.com/Database%20Systems/_git/MLOS/pullrequest/377907
    Goals/Motivations:
    1. RandomForest models are not well suited for extrapolation. As shown in the publication referenced above
        the RERF Lasso model tries to correct this by using the polynomial basis Lasso regression as the
        base model in a boosted model approach.
    2. In the presence of noisy target values (y), the Lasso model will create a global smoothing effect, seen
        to accelerate discovery of optimal solutions faster than Hutter et al. ROAR (random_near_incumbent).
    3. Lasso model's polynomial basis functions mean the gradient to the Lasso model are polynomial.  Hence
        gradients can be computed at any input (X) point using matrix multiplication and eliminating need for
        numerical gradient estimations.
    4. The RandomForest model in RERF fits the Lasso model's residuals, hence any overall regression pattern
        (polynomial includes linear) within a decision tree's leaf data may have been eliminated
        by the Lasso fit.
    """

    _PREDICTOR_OUTPUT_COLUMNS = [
        Prediction.LegalColumnNames.IS_VALID_INPUT,
        Prediction.LegalColumnNames.PREDICTED_VALUE,
        Prediction.LegalColumnNames.PREDICTED_VALUE_VARIANCE,
        Prediction.LegalColumnNames.PREDICTED_VALUE_DEGREES_OF_FREEDOM
    ]

    @trace()
    def __init__(
            self,
            model_config: Point,
            input_space: Hypergrid,
            output_space: Hypergrid,
            logger: logging.Logger = None
    ):
        if logger is None:
            logger = create_logger("RegressionEnhancedRandomForestRegressionModel")
        self.logger = logger

        assert model_config in regression_enhanced_random_forest_config_store.parameter_space
        RegressionModel.__init__(
            self,
            model_type=type(self),
            model_config=model_config,
            input_space=input_space,
            output_space=output_space
        )

        self.model_config = model_config
        self.model_config.perform_initial_root_model_hyper_parameter_search = True

        # enforce model_config constraints (needed by sklearn regression model classes)
        #  For .lasso_regression_model_config.fit_intercept, the intercept term in added in the design_matrix construction
        #  For .lasso_regression_model_config.normalize, since the random forest would also need the scaled features,
        #     scaling would have to be managed by ReRF directly
        model_config.lasso_regression_model_config.fit_intercept = False
        model_config.lasso_regression_model_config.normalize = False
        if model_config.sklearn_random_forest_regression_model_config.oob_score:
            model_config.sklearn_random_forest_regression_model_config.bootstrap = True

        # Explode continuous dimensions to polynomial features up to model config specified monomial degree
        # am using include_bias to produce constant term (all 1s) column to simplify one hot encoding logic
        self.polynomial_features_adapter = ContinuousToPolynomialBasisHypergridAdapter(
            adaptee=input_space,
            degree=self.model_config.max_basis_function_degree,
            include_bias=True,
            interaction_only=False
        )
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

        self.base_regressor_ = None
        self.random_forest_regressor_ = None
        self.x_is_design_matrix = False

        self.random_forest_kwargs = None
        self.root_model_kwargs = None
        self.detected_feature_indices_ = None
        self.screening_root_model_coef_ = None
        self.fit_X_ = None
        self.partial_hat_matrix_ = None
        self.base_regressor_standard_error_ = None
        self.dof_ = None
        self.variance_estimate_ = None
        self.root_model_gradient_coef_ = None
        self.polynomial_features_powers_ = None

        self.categorical_zero_cols_idx_to_delete_ = None

        self._trained = False
        self.last_refit_iteration_number = None

    @property
    def trained(self) -> bool:
        return self._trained

    @property
    def num_observations_used_to_fit(self):
        return self.last_refit_iteration_number

    @property
    def num_model_coefficients(self):
        num_continuous_features = len(self.continuous_dimension_names)
        num_dummy_vars = len(self.one_hot_encoder_adapter.get_one_hot_encoded_column_names())

        return num_continuous_features * (num_dummy_vars + 1)

    def should_fit(
            self,
            num_samples: int
    ) -> bool:
        # since polynomial basis functions decrease the degrees of freedom (TODO: add reference),
        #  and prediction degrees of freedom = sample size - num coef - 1
        #  need sufficiently many samples to exceed the number of coefficients
        dof = num_samples - self.num_model_coefficients - 1

        return dof > 0

    @trace()
    def fit(
            self,
            feature_values_pandas_frame: pd.DataFrame,
            target_values_pandas_frame: pd.DataFrame,
            iteration_number: int = 0
    ):
        """ Fits the RegressionEnhancedRandomForest
        :param feature_values_pandas_frame:
        :param target_values_pandas_frame:
        :param iteration_number:
        :return:
        """
        features_df = self.one_hot_encoder_adapter.project_dataframe(feature_values_pandas_frame, in_place=False)

        # produce design_matrix (incorporating polynomial basis function expansion + one hot encoding)
        (model_design_matrix, new_column_names) = self._transform_x(features_df)
        self.x_is_design_matrix = True
        # run root regression
        model_design_matrix_dataframe = pd.DataFrame(model_design_matrix, columns=new_column_names)
        self._fit_root_regression(
            model_design_matrix_dataframe,
            target_values_pandas_frame,
            iteration_number=iteration_number
        )

        # compute residuals for random forest regression
        base_predicted_y_dataframe = self.base_regressor_.predict(model_design_matrix_dataframe).get_dataframe()
        predicted_y = base_predicted_y_dataframe[Prediction.LegalColumnNames.PREDICTED_VALUE.value]
        y = target_values_pandas_frame[self.output_dimension_names].to_numpy().reshape(-1)
        y_residuals = y - predicted_y

        # fit random forest on lasso residuals
        self._fit_random_forest_regression(model_design_matrix, y_residuals)

        # retain inverse(fit_X.T * fit_X) to use for confidence intervals on predicted values
        condition_number = np.linalg.cond(model_design_matrix)
        if condition_number > 10.0 ** 10:
            # add small noise to fit_x to remove singularity,
            #  expect prediction confidence to be reduced (wider intervals) by doing this
            self.logger.info(
                f"Adding noise to design matrix used for prediction confidence due to condition number {condition_number} > 10 ** 10."
            )
            model_design_matrix += np.random.normal(0, 10.0 ** -4, size=model_design_matrix.shape)
            condition_number = np.linalg.cond(model_design_matrix)
            self.logger.info(
                f"Resulting condition number {condition_number}."
            )
        x_transpose_times_x = np.matmul(model_design_matrix.T, model_design_matrix)
        self.partial_hat_matrix_ = np.linalg.inv(x_transpose_times_x)

        # retain standard error from base model (used for prediction confidence intervals)
        residual_sum_of_squares = np.sum(y_residuals ** 2)
        dof = model_design_matrix.shape[0] - (len(self.base_regressor_.coef_) + 1)  # +1 for intercept
        self.base_regressor_standard_error_ = residual_sum_of_squares / float(dof)

        # values needed to compute total model prediction intervals
        #  TODO : need to determine full RERF model (w/ RF) degrees of freedom
        residual_sum_of_squares = np.sum(y_residuals ** 2)
        self.dof_ = model_design_matrix.shape[0] - len(self.base_regressor_.coef_)
        self.variance_estimate_ = residual_sum_of_squares / float(self.dof_)

        # set status bools so 1) model knows its been trained, and 2) next call to predict creates design_matrix from input space
        self._trained = True
        self.x_is_design_matrix = False
        self.last_refit_iteration_number = iteration_number

        return self

    # this resolves the requested root RegressionModel and calls it
    def _fit_root_regression(
            self,
            x: pd.DataFrame,
            y: pd.DataFrame,
            iteration_number: int
    ):
        # TODO : Add back RidgeCV option after creating RidgeCrossValidatedRegressionModel
        assert \
            self.model_config.boosting_root_model_name in [
                LassoCrossValidatedRegressionModel.__name__
            ], f'Unrecognized boosting_root_model_name {self.model_config.boosting_root_model_name}'

        # Since the RERF transform_x created the proper design_matrix, this serves as the input space for the root regression model.
        # Hence the code below creates a (temporary) hypergrid reflecting the design_matrix.
        # This is less than ideal solution, but deriving min and max of polynomial terms (given feature column degrees) is non-trivial
        # TODO: set bounds on the polynomial terms correctly and eliminate the hack forcing the base_regressor to skip filtering invalid features
        design_matrix_hypergrid = SimpleHypergrid(
            name='RegressionEnhanceRandomForest_design_matrix',
            dimensions=None
        )
        for design_matrix_column_name in x.columns.values:
            design_matrix_dimension = ContinuousDimension(
                name=design_matrix_column_name,
                min=x[design_matrix_column_name].min(),
                max=x[design_matrix_column_name].max()
            )
            design_matrix_hypergrid.add_dimension(design_matrix_dimension)

        # fit lasso/ridge model using either specified params from __init__  or hyper-parameter search
        if self.model_config.boosting_root_model_name == LassoCrossValidatedRegressionModel.__name__:
            root_model_config = self.model_config.dimension_value_dict['lasso_regression_model_config']
            self.base_regressor_ = LassoCrossValidatedRegressionModel(
                model_config=root_model_config,
                input_space=design_matrix_hypergrid,
                output_space=self.output_space
            )
            # skips filtering to valid features in the base_regressor since the valid range of design_matrix column values is incorrect above
            self.base_regressor_.skip_input_filtering_on_predict = True

        self.base_regressor_.fit(
            x,
            y,
            iteration_number=iteration_number
        )

        return self

    def _fit_random_forest_regression(
            self,
            x,
            y_residuals
    ):
        # Assumes x has already been transformed and the reduced feature space and residuals relative to base model
        #  are passed to the random forest regression
        if self.model_config.perform_initial_random_forest_hyper_parameter_search:
            self._execute_grid_search_for_random_forest_regressor_model(x, y_residuals)

        else:
            #self.random_forest_regressor_ = RandomForestRegressor(**self.random_forest_kwargs)
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
            self.random_forest_regressor_.fit(x, y_residuals)

        self.random_forest_kwargs = self.random_forest_regressor_.get_params()

        return self

    def _execute_grid_search_for_random_forest_regressor_model(
            self,
            x,
            y_residuals
    ):
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

        num_features = x.shape[1]
        max_feature_param = [1]
        p_floor_3 = round(num_features / 3)
        if p_floor_3 > 0:
            max_feature_param = np.array([int(0.5 * p_floor_3), int(p_floor_3), int(2 * p_floor_3)])
            max_feature_param = list(np.unique(np.where(max_feature_param == 0, 1, max_feature_param)))
        rf_params = {
            'min_samples_leaf': [5, 10],
            'n_estimators': [10, 50, 100],
            'max_features': max_feature_param
        }
        self.logger.info(f"Performing Random Forest Grid Search CV")
        rf_gscv = GridSearchCV(self.random_forest_regressor_, rf_params)
        rf_gscv.fit(x, y_residuals)

        # retrieve best random forest model and hyper parameters
        self.random_forest_regressor_ = rf_gscv.best_estimator_
        self.random_forest_kwargs = rf_gscv.best_params_

        # only perform hyper-parameter search on first fit
        self.model_config.perform_initial_random_forest_hyper_parameter_search = False

    @trace()
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
        model_design_matrix: np.ndarray = np.array([])
        model_design_matrix_dataframe: pd.DataFrame = pd.DataFrame()
        if self.trained:
            feature_values_pandas_frame = self.input_space.filter_out_invalid_rows(original_dataframe=feature_values_pandas_frame, exclude_extra_columns=False)

            if self.x_is_design_matrix:
                model_design_matrix = feature_values_pandas_frame.to_numpy()
                model_design_matrix_dataframe = feature_values_pandas_frame
            else:
                features_df = self.one_hot_encoder_adapter.project_dataframe(feature_values_pandas_frame, in_place=False)
                (model_design_matrix, new_column_names) = self._transform_x(features_df)
                model_design_matrix_dataframe = pd.DataFrame(model_design_matrix, columns=new_column_names)
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

            base_predictions_dataframe = self.base_regressor_.predict(model_design_matrix_dataframe).get_dataframe()
            residual_predictions = self.random_forest_regressor_.predict(model_design_matrix)
            prediction_dataframe[predicted_value_col] = base_predictions_dataframe[predicted_value_col] + residual_predictions
            prediction_dataframe[dof_col] = self.dof_

            # compute variance needed for prediction interval
            var_list = []
            for _, xi in model_design_matrix_dataframe.iterrows():
                leverage_x = np.matmul(np.matmul(xi.T, self.partial_hat_matrix_), xi)
                prediction_var = self.base_regressor_standard_error_ * (1.0 + leverage_x)
                var_list.append(prediction_var if prediction_var > 0 else 0)

            prediction_dataframe[predicted_value_var_col] = var_list
        predictions.validate_dataframe(prediction_dataframe)

        if not include_only_valid_rows:
            predictions.add_invalid_rows_at_missing_indices(desired_index=feature_values_pandas_frame.index)

        return predictions

    # return design matrix associated with polynomial basis function expansion and one hot encoding
    def _transform_x(
            self,
            x_df: pd.DataFrame
    ) -> (np.ndarray, List[str]):
        # confirm feature_values_pandas_frame contains all expected columns
        #  if any are missing, impute NaN values
        missing_column_names = set.difference(set(self._projected_input_dimension_names), set(x_df.columns.values))
        for missing_column_name in missing_column_names:
            x_df[missing_column_name] = np.NaN

        # impute 0s for NaNs (NaNs can come from hierarchical hypergrids)
        x_df.fillna(value=0, inplace=True)

        # construct traditional design matrix when fitting with one hot encoded categorical dimensions
        if len(self.one_hot_encoder_adapter.get_one_hot_encoded_column_names()) > 0:
            (design_matrix, new_column_names) = self._create_one_hot_encoded_design_matrix(x_df)
        else:
            design_matrix = x_df.to_numpy()
            new_column_names = x_df.columns.values

        return design_matrix, new_column_names

    def _create_one_hot_encoded_design_matrix(
            self,
            x: pd.DataFrame
    ) -> (np.ndarray, List[str]):
        assert len(self.one_hot_encoder_adapter.get_one_hot_encoded_column_names()) > 0
        new_column_names = []

        # use the following to create one hot encoding columns prior to constructing fit_x and powers_ table
        num_continuous_features = len(self.continuous_dimension_names)
        continuous_features_x = x[self.continuous_dimension_names]
        new_column_names.extend(continuous_features_x)

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

            added_column_names = [cont_name + '*' + ohe_col_name for cont_name in continuous_features_x]

            new_column_names.extend(added_column_names)
        fit_x_dataframe = pd.DataFrame(fit_x, columns=new_column_names)

        # check for zero columns (expected with hierarchical feature hypergrids containing NaNs for some features)
        #  this should eliminate singular design matrix errors from lasso/ridge regressions
        if self.categorical_zero_cols_idx_to_delete_ is None:
            self.categorical_zero_cols_idx_to_delete_ = np.argwhere(np.all(fit_x[..., :] == 0, axis=0))

        # remembered from .fit() if not set above
        zero_cols_idx = self.categorical_zero_cols_idx_to_delete_
        if zero_cols_idx.any():
            drop_column_names = [new_column_names[i] for i in list(zero_cols_idx.flatten())]
            fit_x_dataframe.drop(columns=drop_column_names, inplace=True)
            new_column_names = fit_x_dataframe.columns.values

        fit_x = fit_x_dataframe.to_numpy()

        return fit_x, new_column_names

#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from typing import List
import numpy as np

from sklearn.utils.validation import check_is_fitted
from sklearn import linear_model
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
from sklearn.model_selection import GridSearchCV
from sklearn.preprocessing import StandardScaler

from mlos.Logger import create_logger
from mlos.Optimizers.RegressionModels.RegressionModel import RegressionModel
from mlos.Optimizers.RegressionModels.Prediction import Prediction
from mlos.Optimizers.RegressionModels.SklearnLassoRegressionModelConfig import SklearnLassoRegressionModelConfig
from mlos.Optimizers.RegressionModels.SklearnRidgeRegressionModelConfig import SklearnRidgeRegressionModelConfig
from mlos.Optimizers.RegressionModels.SklearnRandomForestRegressionModelConfig import SklearnRandomForestRegressionModelConfig
from mlos.Spaces import Hypergrid, SimpleHypergrid, ContinuousDimension, DiscreteDimension, CategoricalDimension, Point
from mlos.Spaces.Configs.DefaultConfigMeta import DefaultConfigMeta
from mlos.Spaces.HypergridAdapters.CategoricalToOneHotEncodedHypergridAdapter import CategoricalToOneHotEncodedHypergridAdapter
from mlos.Spaces.HypergridAdapters.ContinuousToPolynomialBasisHypergridAdapter import ContinuousToPolynomialBasisHypergridAdapter
from mlos.Tracer import trace


class RegressionEnhancedRandomForestRegressionModelPrediction(Prediction):
    all_prediction_fields = Prediction.LegalColumnNames
    OUTPUT_FIELDS: List[Prediction.LegalColumnNames] = [
        all_prediction_fields.PREDICTED_VALUE,
        all_prediction_fields.PREDICTED_VALUE_VARIANCE,
        all_prediction_fields.DEGREES_OF_FREEDOM]

    def __init__(self, objective_name: str):
        super().__init__(objective_name=objective_name, predictor_outputs=RegressionEnhancedRandomForestRegressionModelPrediction.OUTPUT_FIELDS)


class RegressionEnhancedRandomForestRegressionModelConfig(metaclass=DefaultConfigMeta):
    """A configuration object for RERF model.

    Class responsible for validating its objects are valid hyper parameters for the sklearn classes:
       Lasso (https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.Lasso.html),
       Ridge
        (https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.Ridge.html#sklearn.linear_model.Ridge)
    and
       RandomForest ()
    """

    CONFIG_SPACE = SimpleHypergrid(
        name="regression_enhanced_random_forest_regression_model_config",
        dimensions=[
            DiscreteDimension(name="max_basis_function_degree", min=1, max=10),
            CategoricalDimension(name="residual_model_name",
                                 values=[SklearnRandomForestRegressionModelConfig.__name__]),
            CategoricalDimension(name="boosting_root_model_name",
                                 values=[SklearnLassoRegressionModelConfig.__name__,
                                         SklearnRidgeRegressionModelConfig.__name__]),
            ContinuousDimension(name="min_abs_root_model_coef", min=0, max=2 ** 10),
            CategoricalDimension(name="perform_initial_root_model_hyper_parameter_search", values=[False, True]),
            CategoricalDimension(name="perform_initial_random_forest_hyper_parameter_search", values=[False, True])
        ]
    ).join(
        subgrid=SklearnLassoRegressionModelConfig.CONFIG_SPACE,
        on_external_dimension=CategoricalDimension(name="boosting_root_model_name",
                                                   values=[SklearnLassoRegressionModelConfig.__name__])
    ).join(
        subgrid=SklearnRidgeRegressionModelConfig.CONFIG_SPACE,
        on_external_dimension=CategoricalDimension(name="boosting_root_model_name",
                                                   values=[SklearnRidgeRegressionModelConfig.__name__])
    ).join(
        subgrid=SklearnRandomForestRegressionModelConfig.CONFIG_SPACE,
        on_external_dimension=CategoricalDimension(name="residual_model_name",
                                                   values=[SklearnRandomForestRegressionModelConfig.__name__])
    )

    _DEFAULT = Point(
        max_basis_function_degree=2,
        residual_model_name=SklearnRandomForestRegressionModelConfig.__name__,
        boosting_root_model_name=SklearnLassoRegressionModelConfig.__name__,
        min_abs_root_model_coef=0.01,
        sklearn_lasso_regression_model_config=SklearnLassoRegressionModelConfig.DEFAULT,
        sklearn_ridge_regression_model_config=SklearnRidgeRegressionModelConfig.DEFAULT,
        sklearn_random_forest_regression_model_config=SklearnRandomForestRegressionModelConfig.DEFAULT,
        perform_initial_root_model_hyper_parameter_search=True,
        perform_initial_random_forest_hyper_parameter_search=True
    )

    @classmethod
    def contains(cls, config):
        return config in cls.CONFIG_SPACE


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
        gradients can be computed at any input (X) point using matrix multiplication and eliminaing need for
        numerical gradient estimations.
    4. The RandomForest model in RERF fits the Lasso model's residuals, hence any overall regression pattern
        (polynomial includes linear) within a decision tree's leaf data may have been eliminated
        by the Lasso fit.

    """

    @trace()
    def __init__(
            self,
            model_config: Point,
            input_space: Hypergrid,
            output_space: Hypergrid,
            logger=None
    ):
        if logger is None:
            logger = create_logger("RegressionEnhancedRandomForestRegressionModel")
        self.logger = logger

        assert model_config in RegressionEnhancedRandomForestRegressionModelConfig.CONFIG_SPACE

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
            adaptee=input_space,
            merge_all_categorical_dimensions=True,
            drop='first'
        )
        # Explode continuous dimensions to polynomial features up to model config specified monomial degree
        # am using include_bias to produce constant term (all 1s) column to simplify one hot encoding logic
        self.polynomial_features_adapter = ContinuousToPolynomialBasisHypergridAdapter(
            adaptee=self.one_hot_encoder_adapter,
            degree=self.model_config.max_basis_function_degree,
            include_bias=True,
            interaction_only=False
        )
        self.input_space = input_space

        self.input_dimension_names = [dimension.name for dimension in self.input_space.dimensions]
        self.output_dimension_names = [dimension.name for dimension in self.output_space.dimensions]

        self.base_regressor_ = None
        self.random_forest_regressor_ = None

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
        self.scaler_ = StandardScaler()

        self._trained = False

    @property
    def trained(self):
        return self._trained

    @trace()
    def fit(self, feature_values_pandas_frame, target_values_pandas_frame, iteration_number=0):
        """ Fits the RegressionEnhancedRandomForest

            The issue here is that the feature_values will come in as a numpy array where each column corresponds to one
            of the dimensions in our input space. The target_values will come in a similar numpy array with each column
            corresponding to a single dimension in our output space.

            Our goal is to slice them up and feed the observations to individual decision trees.

        :param feature_values_pandas_frame:
        :param target_values_pandas_frame:
        :return:
        """
        y = target_values_pandas_frame[self.output_dimension_names].to_numpy().reshape(-1)
        fit_x = self.transform_x(feature_values_pandas_frame, what_to_return='fit_x')

        # run root regression
        self._fit_root_regression(fit_x, y)

        # restrict X to features selected from lasso/Ridge regression
        x_filtered_to_detected_features = self._filter_to_detected_features(fit_x)

        # compute residuals for random forest regression
        base_predicted_y = self.base_regressor_.predict(x_filtered_to_detected_features).reshape(-1)
        y_residuals = y - base_predicted_y

        # fit random forest on lasso residuals
        self._fit_random_forest_regression(x_filtered_to_detected_features, y_residuals)

        # retain inverse(fit_X.T * fit_X) to use for confidence intervals on predicted values
        condition_number = np.linalg.cond(x_filtered_to_detected_features)
        if condition_number > 10.0 ** 10:
            # add small noise to fit_x to remove singularity,
            #  expect prediction confidence to be reduced (wider intervals) by doing this
            self.logger.info(
                f"Adding noise to design matrix used for prediction confidence due to condition number {condition_number} > 10^10."
            )
            x_filtered_to_detected_features += np.random.normal(0, 10.0**-4, size=x_filtered_to_detected_features.shape)
            condition_number = np.linalg.cond(x_filtered_to_detected_features)
            self.logger.info(
                f"Resulting condition number {condition_number}."
            )
        x_transpose_times_x = np.matmul(x_filtered_to_detected_features.T, x_filtered_to_detected_features)
        self.partial_hat_matrix_ = np.linalg.inv(x_transpose_times_x)

        # retain standard error from base model (used for prediction confidence intervals)
        base_predicted_y = self.base_regressor_.predict(x_filtered_to_detected_features)
        base_residual_y = y - base_predicted_y
        residual_sum_of_squares = np.sum(base_residual_y ** 2)
        dof = fit_x.shape[0] - (len(self.base_regressor_.coef_) + 1)  # +1 for intercept
        self.base_regressor_standard_error_ = residual_sum_of_squares / float(dof)

        # values needed to compute total model prediction intervals
        #  TODO : need to determine full RERF model (w/ RF) degrees of freedom
        residual_sum_of_squares = np.sum(y_residuals ** 2)
        self.dof_ = fit_x.shape[0] - len(self.base_regressor_.coef_)
        self.variance_estimate_ = residual_sum_of_squares / float(self.dof_)

        self._trained = True
        return self

    def _fit_root_regression(self, x, y):
        # Assumes x has already been transformed
        self.detected_feature_indices_ = []

        if self.model_config.perform_initial_root_model_hyper_parameter_search:
            # tune hyper parameters via k-fold cross validation
            self._execute_grid_search_for_base_regressor_model(x, y)

        else:
            # fit lasso/ridge model using either specified params from __init__  or hyper-parameter search
            if self.model_config.boosting_root_model_name == SklearnLassoRegressionModelConfig.__name__:
                self.base_regressor_ = linear_model.Lasso(**self.root_model_kwargs)
            elif self.model_config.boosting_root_model_name == SklearnRidgeRegressionModelConfig.__name__:
                self.base_regressor_ = linear_model.Ridge(**self.root_model_kwargs)
            self.base_regressor_.fit(x, y)

            self.screening_root_model_coef_ = self.base_regressor_.coef_

        # ET TODO: capping minimum coef seems to go against the spirit of Lasso/Ridge identifying features
        #  So need to understand if this is needed
        self.detected_feature_indices_ = np.where(np.abs(self.screening_root_model_coef_) >= self.model_config.min_abs_root_model_coef)[0]
        self.base_regressor_.coef_ = self.base_regressor_.coef_[self.detected_feature_indices_]

        # define coef for gradient to polynomial fit
        self._set_polynomial_gradient_coef()

        return self

    def _execute_grid_search_for_base_regressor_model(self, x, y):
        model_config = self.model_config
        if self.model_config.boosting_root_model_name == SklearnLassoRegressionModelConfig.__name__:
            self.base_regressor_ = linear_model.Lasso(
                alpha=model_config.sklearn_lasso_regression_model_config.alpha,
                fit_intercept=model_config.sklearn_lasso_regression_model_config.fit_intercept,
                normalize=model_config.sklearn_lasso_regression_model_config.normalize,
                precompute=model_config.sklearn_lasso_regression_model_config.precompute,
                copy_X=model_config.sklearn_lasso_regression_model_config.copy_x,
                max_iter=model_config.sklearn_lasso_regression_model_config.max_iter,
                tol=model_config.sklearn_lasso_regression_model_config.tol,
                warm_start=model_config.sklearn_lasso_regression_model_config.warm_start,
                positive=model_config.sklearn_lasso_regression_model_config.positive,
                random_state=None,
                selection=model_config.sklearn_lasso_regression_model_config.selection
            )
        elif self.model_config.boosting_root_model_name == SklearnRidgeRegressionModelConfig.__name__:
            self.base_regressor_ = linear_model.Ridge(
                alpha=model_config.sklearn_ridge_regression_model_config.alpha,
                fit_intercept=model_config.sklearn_ridge_regression_model_config.fit_intercept,
                normalize=model_config.sklearn_ridge_regression_model_config.normalize,
                copy_X=model_config.sklearn_ridge_regression_model_config.copy_x,
                max_iter=model_config.sklearn_ridge_regression_model_config.max_iter,
                tol=model_config.sklearn_ridge_regression_model_config.tol,
                random_state=None,
                solver=model_config.sklearn_ridge_regression_model_config.solver
            )
        else:
            self.logger('Boosting base model name "{0}" not supported currently.' \
                        .format(self.model_config.boosting_root_model_name))

        # hard wiring which model hyper parameters are used for model optimization
        tunable_hyper_params = {
            SklearnLassoRegressionModelConfig.__name__: {
                'alpha': np.exp([np.log(0.001) + h * (np.log(100) - np.log(0.001)) / 100 for h in range(100)])
            },
            SklearnRidgeRegressionModelConfig.__name__: {
                'alpha': np.exp([np.log(0.001) + h * (np.log(100) - np.log(0.001)) / 100 for h in range(100)])
            }
        }

        root_model_gscv = GridSearchCV(
            self.base_regressor_,
            tunable_hyper_params[self.model_config.boosting_root_model_name])
        root_model_gscv.fit(x, y)

        # retain best lasso/Ridge model
        self.base_regressor_ = root_model_gscv.best_estimator_

        # retain hyper-params search results in case we want to re-use these w/o search
        self.root_model_kwargs = self.base_regressor_.get_params()

        # restrict X to features detected with Lasso regression
        #  this is X* in the original paper and will be used for the random forest fit
        #  since X* is the input for both models, the index list will be needed for predict method
        self.screening_root_model_coef_ = self.base_regressor_.coef_

        # only perform hyper-parameter search on first fit
        self.model_config.perform_initial_root_model_hyper_parameter_search = False

    def _fit_random_forest_regression(self, x_star, y_residuals):
        # Assumes x has already been transformed and the reduced feature space and residuals relative to base model
        #  are passed to the random forest regression
        if self.model_config.perform_initial_random_forest_hyper_parameter_search:
            self._execute_grid_search_for_random_forest_regressor_model(x_star, y_residuals)

        else:
            self.random_forest_regressor_ = RandomForestRegressor(**self.random_forest_kwargs)
            self.random_forest_regressor_.fit(x_star, y_residuals)

        self.random_forest_kwargs = self.random_forest_regressor_.get_params()

        return self

    def _execute_grid_search_for_random_forest_regressor_model(self, x_filtered_to_detected_features, y_residuals):
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

        num_features = x_filtered_to_detected_features.shape[1]
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

        rf_gscv = GridSearchCV(self.random_forest_regressor_, rf_params)
        rf_gscv.fit(x_filtered_to_detected_features, y_residuals)

        # retrieve best random forest model and hyper parameters
        self.random_forest_regressor_ = rf_gscv.best_estimator_

        # only perform hyper-parameter search on first fit
        self.model_config.perform_initial_random_forest_hyper_parameter_search = False

    @trace()
    def predict(self, feature_values_pandas_frame, include_only_valid_rows=True):
        check_is_fitted(self)

        x_filtered_to_detected_features = self.transform_x(feature_values_pandas_frame)

        base_predicted = self.base_regressor_.predict(x_filtered_to_detected_features)
        residual_predicted = self.random_forest_regressor_.predict(x_filtered_to_detected_features)
        y_predicted = base_predicted + residual_predicted

        # dataframe column shortcuts
        predicted_value_col = Prediction.LegalColumnNames.PREDICTED_VALUE.value
        predicted_value_var_col = Prediction.LegalColumnNames.PREDICTED_VALUE_VARIANCE.value
        predicted_value_dof_col = Prediction.LegalColumnNames.DEGREES_OF_FREEDOM.value

        # initialize return predictions
        predictions = RegressionEnhancedRandomForestRegressionModelPrediction(objective_name=self.output_dimension_names[0])
        prediction_df = predictions.get_dataframe()

        prediction_df[predicted_value_col] = y_predicted
        prediction_df[predicted_value_dof_col] = self.dof_

        # compute variance needed for prediction interval
        var_list = []
        for xi in x_filtered_to_detected_features:
            leverage_x = np.matmul(np.matmul(xi.T, self.partial_hat_matrix_), xi)
            prediction_var = self.base_regressor_standard_error_ * (1.0 + leverage_x)
            var_list.append(prediction_var)

        prediction_df[predicted_value_var_col] = var_list
        predictions.set_dataframe(prediction_df)
        return predictions

    def score(self, feature_values_pandas_frame, target_values_pandas_frame):
        x_df = feature_values_pandas_frame[self.input_dimension_names]
        y = target_values_pandas_frame[self.output_dimension_names].to_numpy()

        predictions = self.predict(x_df)
        predictions_df = predictions.get_dataframe()
        r2 = r2_score(y, predictions_df[Prediction.LegalColumnNames.PREDICTED_VALUE.value])
        return r2

    def _set_categorical_powers_table(self,
                                      num_continuous_dims=0,
                                      num_categorical_levels=0,
                                      num_terms_in_poly=0,
                                      num_dummy_vars=0,
                                      zero_cols_idx=None):
        """
        _set_categorical_powers_table() defines a table (similar to PolynomialFeature.powers_ indicating
           the power of a feature associated with each term in the polynomial expansion created by _create_one_hot_encoded_design_matrix()
        If no dummy variables are present, this table is already set using self.polynomial_features_adapter.get_polynomial_feature_powers_table().
        The presence of categorical features increases dimensionality of the feature space
          (in addition to the basis function expansion), and hence the equivalent .powers_ table needs to be constructed.

        param zero_cols_index:
        Since the Hierarchical HyperGrid feature spaces can have missing feature values, the
        the dummy variable creation process produces design matrices with columns of
        zeros (singular matrices), which are detected and dropped in _create_one_hot_encoded_design_matrix().
        Passing the indices of these zero columns with as arg zero_cols_index allows those dropped
        derived features to also be removed from the internal copy of the ".powers_" table.
        """
        base_powers_ = self.polynomial_features_adapter.get_polynomial_feature_powers_table()
        self.polynomial_features_powers_ = np.zeros((num_terms_in_poly * num_categorical_levels,
                                                     num_dummy_vars + num_continuous_dims))

        for i in range(num_categorical_levels):
            row_index_min = i * num_terms_in_poly
            row_index_max = (i + 1) * num_terms_in_poly
            col_index_max = num_continuous_dims
            self.polynomial_features_powers_[row_index_min:row_index_max, 0:col_index_max] = base_powers_

            if i > 0:
                col_index_min = col_index_max + i - 1
                self.polynomial_features_powers_[row_index_min:row_index_max,
                                                 col_index_min:col_index_min + 1] = np.ones((num_terms_in_poly, 1))

        # deal with Hierarchical HyperGrid hat matrix singularities
        if zero_cols_idx is not None:
            self.polynomial_features_powers_ = np.delete(self.polynomial_features_powers_, zero_cols_idx, axis=0)

    def transform_x(self, x, what_to_return='x_star'):
        """
        transform_x performs 3 operations as part of preparing the input feature dataframe for RERF fit()/predict():
          1. Impute 0s for NaNs.  This case arises in hierarchical hypergrids where dimensions are not shared
             across categorical levels.  Since the presence of zero columns in the design matrix makes the p-hat matrix
             singular, fit() method eliminates those columns.
          2. "Explodes" the initial feature space using the specified polynomial basis functions.
          3. Once Lasso/Ridge regression identifies feature dimensions of little predictive value, those dimensions
             are "filtered" from the expanded feature space.
        """
        # confirm feature_values_pandas_frame contains all expected columns
        #  if any are missing, impute NaN values
        missing_column_names = set.difference(set(self.input_dimension_names), set(x.columns.values))
        for missing_column_name in missing_column_names:
            x[missing_column_name] = np.NaN

        x_df = self.polynomial_features_adapter.project_dataframe(df=x, in_place=True)

        # impute 0s for NaNs (NaNs can come from hierarchical hypergrids)
        x_df.fillna(value=0, inplace=True)
        if len(self.one_hot_encoder_adapter.get_one_hot_encoded_column_names()) > 0:
            fit_x = self._create_one_hot_encoded_design_matrix(x_df)
        else:
            fit_x = x_df.to_numpy()
            self.polynomial_features_powers_ = self.polynomial_features_adapter.get_polynomial_feature_powers_table()
        self.fit_X_ = fit_x

        if what_to_return.upper() == 'fit_x'.upper():
            return fit_x

        # restrict to features selected by previous lasso fit
        #   serve as inputs to both regression and random forest on the residuals
        x_filtered_to_discovered_features = self._filter_to_detected_features(fit_x)

        return x_filtered_to_discovered_features

    def _create_one_hot_encoded_design_matrix(self, x):
        assert len(self.one_hot_encoder_adapter.get_one_hot_encoded_column_names()) > 0

        # use the following to create one hot encoding columns prior to constructing fit_x and powers_ table
        continuous_dim_col_names = self.polynomial_features_adapter.get_column_names_for_polynomial_features(degree=1)
        polynomial_features_x = x[self.polynomial_features_adapter.get_column_names_for_polynomial_features()]

        dummy_var_cols = self.one_hot_encoder_adapter.get_one_hot_encoded_column_names()
        num_dummy_vars = len(dummy_var_cols)
        num_terms_in_poly = self.polynomial_features_adapter.get_num_polynomial_features()

        # initialize the design matrix
        fit_x = np.zeros((x.shape[0], num_terms_in_poly * (num_dummy_vars + 1)))

        # add polynomial features weighted by oneHotEncoded columns
        # add polynomial for 000...000 encoding
        fit_x[:, 0:num_terms_in_poly] = polynomial_features_x.copy().to_numpy()

        # add ohe * polynomial terms for non-000...000 encodings
        last_col_filled = num_terms_in_poly
        for ohe_col_name in dummy_var_cols:
            fit_x[:, last_col_filled:last_col_filled + num_terms_in_poly] = x[ohe_col_name].to_numpy().reshape(-1, 1) * polynomial_features_x.copy().to_numpy()
            last_col_filled += num_terms_in_poly

        # check for zero columns (expected with hierarchical feature hypergrids containing NaNs for some features)
        #  this should eliminate singular design matrix errors from lasso/ridge regressions
        if self.categorical_zero_cols_idx_to_delete_ is None:
            self.categorical_zero_cols_idx_to_delete_ = np.argwhere(np.all(fit_x[..., :] == 0, axis=0))
        zero_cols_idx = self.categorical_zero_cols_idx_to_delete_
        if zero_cols_idx.any():
            fit_x = np.delete(fit_x, zero_cols_idx, axis=1)

        # construct the regressor_model.powers_ table to enable construction of algebraic gradients
        if self.polynomial_features_powers_ is None:
            self._set_categorical_powers_table(
                num_continuous_dims=len(continuous_dim_col_names),
                num_categorical_levels=num_dummy_vars+1,
                num_terms_in_poly=num_terms_in_poly,
                num_dummy_vars=num_dummy_vars,
                zero_cols_idx=zero_cols_idx
            )

        return fit_x

    def _filter_to_detected_features(self, fit_x):
        x_filtered_to_detected_features = fit_x[:, self.detected_feature_indices_]
        return x_filtered_to_detected_features

    def _set_polynomial_gradient_coef(self):
        gradient_coef_matrix = []

        fit_coef = self.base_regressor_.coef_  # this skips the intercept term, for which all powers_ values = 0
        fit_poly_powers = self.polynomial_features_powers_
        restricted_features = self.detected_feature_indices_

        # transpose of powers reflect the polynomial powers for polynomial F
        #  since these powers become the multiplier in the gradient with respect to x_i,
        #  they make computing the gradient direct.
        # See details of powers array :
        #   https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.PolynomialFeatures.html
        powers_t = np.transpose(fit_poly_powers)
        for powers_wrt_xj in powers_t:
            grad_coef_row = []
            j = 0
            for i, ip in enumerate(powers_wrt_xj):
                if i in restricted_features:
                    p = ip  # powers_wrt_xj[i]
                    c = fit_coef[j]
                    if p > 0:  # if p > 0, X_j contributes X_j**p to F polynomial
                        grad_coef_row.append(p * c)
                    j += 1

            # since highest powered X_j will not appear in gradient polynomial,
            #  but still want X * gradient_matrix to work, pad gradient_matrix with zeros
            # The +1 accounts for the leading 1 in fit_X transformed features but not recorded in lasso coef_
            while len(grad_coef_row) < len(fit_coef) + 1:
                grad_coef_row.append(0)

            # add partial fit poly wrt X_j polynomial coefficients to final matrix
            gradient_coef_matrix.append(grad_coef_row)
        gradient_coef_matrix = np.transpose(gradient_coef_matrix)

        num_terms_in_poly = len(fit_poly_powers)
        num_dim = len(fit_poly_powers[0])
        augmented_grad_poly_coef = np.zeros((num_terms_in_poly, num_dim))
        for j, term_used_index in enumerate(restricted_features):
            for i in range(num_dim):
                augmented_grad_poly_coef[term_used_index - 1, i] = gradient_coef_matrix[j, i]

        self.root_model_gradient_coef_ = augmented_grad_poly_coef

    def gradient_at_x(self, x):
        fit_x = self._create_one_hot_encoded_design_matrix(x)
        gradient_at_x = np.matmul(fit_x, self.root_model_gradient_coef_)
        return gradient_at_x

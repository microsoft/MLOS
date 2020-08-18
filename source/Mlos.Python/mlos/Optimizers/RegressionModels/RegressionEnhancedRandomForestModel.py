#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#

import numpy as np
from sklearn.utils.validation import check_X_y, check_array, check_is_fitted
from sklearn import linear_model
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
from sklearn.model_selection import GridSearchCV
from sklearn.preprocessing import PolynomialFeatures

from mlos.Spaces import Dimension, Hypergrid, SimpleHypergrid, \
    ContinuousDimension, DiscreteDimension, CategoricalDimension, Point
from mlos.Tracer import trace
from mlos.Logger import create_logger

from .RegressionModel import RegressionModel, RegressionModelConfig
from .Prediction import Prediction
from .SklearnLassoRegressionModelConfig import SklearnLassoRegressionModelConfig
from .SklearnRidgeRegressionModelConfig import SklearnRidgeRegressionModelConfig
from .SklearnRandomForestRegressionModelConfig import\
    SklearnRandomForestRegressionModelConfig



# sklearn injects many warnings, so from
#   https://stackoverflow.com/questions/32612180/eliminating-warnings-from-scikit-learn
# TODO: fix what causes Lasso regression to throw warnings during convergence
#       suspect these result from not standardizing X
#       The following code silences these in Jupyter notebooks, but not sure how best to execute these in Mlos context
#import warnings
# def warn(*args, **kwargs):
#    pass
# warnings.warn = warn


class RegressionEnhancedRandomForestRegressionModelConfig(RegressionModelConfig):
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

    DEFAULT = Point(
        max_basis_function_degree=2,
        residual_model_name=SklearnRandomForestRegressionModelConfig.__name__,
        boosting_root_model_name=SklearnLassoRegressionModelConfig.__name__,
        min_abs_root_model_coef=0.01,
        sklearn_lasso_regression_model_config=SklearnLassoRegressionModelConfig.DEFAULT,
        sklearn_ridge_regression_model_config=SklearnRidgeRegressionModelConfig.DEFAULT,
        sklearn_random_forest_regression_model_config=SklearnRandomForestRegressionModelConfig.DEFAULT,
        perform_initial_root_model_hyper_parameter_search=True,
        perform_initial_random_forest_hyper_parameter_search=False
    )

    @classmethod
    def contains(cls, config):
        return Point(
            max_basis_function_degree=config.max_basis_function_degree,
            residual_model_name=config.residual_model_name,
            boosting_root_model_name=config.boosting_root_model_name,
            min_abs_root_model_coef=config.min_abs_root_model_coef,
            perform_initial_root_model_hyper_parameter_search=config.perform_initial_root_model_hyper_parameter_search,
            perform_initial_random_forest_hyper_parameter_search=config.perform_initial_random_forest_hyper_parameter_search,
        ) in cls.CONFIG_SPACE

    @classmethod
    def create_from_config_point(cls, config_point):
        assert cls.contains(config_point)
        config_key_value_pairs = {param_name: value for param_name, value in config_point}
        return cls(**config_key_value_pairs)

    def __init__(
            self,
            max_basis_function_degree=DEFAULT.max_basis_function_degree,
            boosting_root_model_name=DEFAULT.boosting_root_model_name,
            min_abs_root_model_coef=DEFAULT.min_abs_root_model_coef,
            boosting_root_model_config: Point()=DEFAULT.sklearn_lasso_regression_model_config,
            random_forest_model_config: Point()=DEFAULT.sklearn_random_forest_regression_model_config,
            residual_model_name=DEFAULT.residual_model_name,
            perform_initial_root_model_hyper_parameter_search=DEFAULT.perform_initial_root_model_hyper_parameter_search,
            perform_initial_random_forest_hyper_parameter_search=DEFAULT.perform_initial_random_forest_hyper_parameter_search
    ):
        self.max_basis_function_degree = max_basis_function_degree
        self.residual_model_name = residual_model_name
        self.min_abs_root_model_coef = min_abs_root_model_coef
        self.perform_initial_root_model_hyper_parameter_search = perform_initial_root_model_hyper_parameter_search
        self.perform_initial_random_forest_hyper_parameter_search = perform_initial_random_forest_hyper_parameter_search

        self.boosting_root_model_name = boosting_root_model_name
        self.boosting_root_model_config = None
        if self.boosting_root_model_name == SklearnLassoRegressionModelConfig.__name__:
            self.boosting_root_model_config = SklearnLassoRegressionModelConfig \
                .create_from_config_point(boosting_root_model_config)
        elif self.boosting_root_model_name == SklearnRidgeRegressionModelConfig.__name__:
            self.boosting_root_model_config = SklearnRidgeRegressionModelConfig \
                .create_from_config_point(boosting_root_model_config)
        else:
            print('Unrecognized boosting_root_model_name "{}"'.format(self.boosting_root_model_name))

        self.random_forest_model_config = SklearnRandomForestRegressionModelConfig \
            .create_from_config_point(random_forest_model_config)


class RegressionEnhancedRandomForestRegressionModel(RegressionModel):
    """ Regression-Enhanced RandomForest Regression model

    See https://arxiv.org/pdf/1904.10416.pdf for inspiration.
    See following PRs for exploration notes/observations:

    1. https://msdata.visualstudio.com/Database%20Systems/_git/MLOS/pullrequest/377907


    Goals/Motivations:
    1. RandomForest models are not well suited for extrapolation. As shown in the publication the RERF Lasso model
            corrects helps correct this.
    2. In the presence of noisy target values (y), the Lasso model will create a global smoothing effect, seen
        to accelerate discovery of optimal solutions faster than Hutter et al. ROAR (random_near_incumbent).
    3. Lasso model's polynomial basis functions mean the gradient to the Lasso model are polynomial.  Hence
        gradients can be computed at any input (X) point using matrix multiplication and eliminaing need for
        numerical gradient estimations.
    4. The RandomForest model in RERF fits the Lasso model's residuals, hence any overall regression pattern
        (polynomial so also linear) within a decision tree's leaf data may have been eliminated reduced prior
        by the Lasso fit.

    """

    @trace()
    def __init__(
            self,
            model_config: RegressionEnhancedRandomForestRegressionModelConfig,
            input_space: Hypergrid,
            output_space: Hypergrid,
            logger=None
    ):
        if logger is None:
            logger = create_logger("RegressionEnhancedRandomForestRegressionModel")
        self.logger = logger

        assert RegressionEnhancedRandomForestRegressionModelConfig.contains(model_config)
        super(RegressionEnhancedRandomForestRegressionModel, self).__init__(
            model_type=type(self),
            model_config=model_config
        )
        self.model_config = model_config

        self.input_space = input_space
        self.input_dimension_names = [dimension.name for dimension in self.input_space.dimensions]
        self.output_space = output_space
        self.output_dimension_names = [dimension.name for dimension in self.output_space.dimensions]

        self._input_space_dimension_name_mappings = {
            dimension.name: Dimension.flatten_dimension_name(dimension.name)
            for dimension in self.input_space.dimensions
        }

        self._output_space_dimension_name_mappings = {
            dimension.name: Dimension.flatten_dimension_name(dimension.name)
            for dimension in self.output_space.dimensions
        }

        self.base_regressor_ = None
        self.base_regressor_config = dict()
        self.base_regressor_config = self.model_config.boosting_root_model_config
        if self.model_config.boosting_root_model_name == SklearnLassoRegressionModelConfig.__name__:
            self.base_regressor_ = linear_model.Lasso(
                alpha=self.base_regressor_config.alpha,
                fit_intercept=self.base_regressor_config.fit_intercept,
                normalize=self.base_regressor_config.normalize,
                precompute=self.base_regressor_config.precompute,
                copy_X=self.base_regressor_config.copy_x,
                max_iter=self.base_regressor_config.max_iter,
                tol=self.base_regressor_config.tol,
                warm_start=self.base_regressor_config.warm_start,
                positive=self.base_regressor_config.positive,
                random_state=self.base_regressor_config.random_state,
                selection=self.base_regressor_config.selection

            )
        elif self.model_config.boosting_root_model_name == SklearnRidgeRegressionModelConfig.__name__:
            self.base_regressor_ = linear_model.Ridge(
                alpha=self.base_regressor_config.alpha,
                fit_intercept=self.base_regressor_config.fit_intercept,
                normalize=self.base_regressor_config.normalize,
                copy_X=self.base_regressor_config.copy_x,
                max_iter=self.base_regressor_config.max_iter,
                tol=self.base_regressor_config.tol,
                random_state=self.base_regressor_config.random_state,
                solver=self.base_regressor_config.solver
            )
        else:
            self.logger('Boosting base model name "{0}" not supported currently.' \
                        .format(self.model_config.boosting_root_model_name))

        rf_config = self.model_config.random_forest_model_config
        self.random_forest_regressor_ = RandomForestRegressor(
            n_estimators=rf_config.n_estimators,
            criterion=rf_config.criterion,
            max_depth=rf_config.max_depth_value,
            min_samples_split=rf_config.min_samples_split,
            min_samples_leaf=rf_config.min_samples_leaf,
            min_weight_fraction_leaf=rf_config.min_weight_fraction_leaf,
            max_features=rf_config.max_features,
            max_leaf_nodes=rf_config.max_leaf_nodes_value,
            min_impurity_decrease=rf_config.min_impurity_decrease,
            bootstrap=rf_config.bootstrap,
            oob_score=rf_config.oob_score,
            n_jobs=rf_config.n_jobs,
            warm_start=rf_config.warm_start,
            ccp_alpha=rf_config.ccp_alpha,
            max_samples=rf_config.max_sample_value
        )

        # set up basis feature transform
        self.polynomial_features_transform_ = None
        if self.model_config.max_basis_function_degree > 1:
            self.polynomial_features_transform_ = \
                PolynomialFeatures(degree=self.model_config.max_basis_function_degree)

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

    @trace()
    def fit(self, feature_values_pandas_frame, target_values_pandas_frame):
        """ Fits the RegressionEnhancedRandomForest

            The issue here is that the feature_values will come in as a numpy array where each column corresponds to one
            of the dimensions in our input space. The target_values will come in a similar numpy array with each column
            corresponding to a single dimension in our output space.

            Our goal is to slice them up and feed the observations to individual decision trees.

        :param feature_values_pandas_frame:
        :param target_values_pandas_frame:
        :return:
        """
        self.logger.info(
            f"Fitting a {self.__class__.__name__} with {len(feature_values_pandas_frame.index)} observations.")

        # pull X and y values from data frames passed
        x = feature_values_pandas_frame[self.input_dimension_names].to_numpy()
        y = target_values_pandas_frame[self.output_dimension_names].to_numpy()

        # Check that X and y have correct shape
        x, y = check_X_y(x, y)

        # explode features to requested basis degree for model
        fit_x = self._explode_x(x)
        self.fit_X_ = fit_x

        # run root regression
        self._fit_root_regression(fit_x, y)

        # restrict X to features selected from lasso/Ridge regression
        x_star = self._filter_to_detected_features(fit_x)

        # compute residuals for random forest regression
        y_residuals = y - self.base_regressor_.predict(x_star)

        # fit random forest on lasso residuals
        self._fit_random_forest_regression(x_star, y_residuals)

        # retain inverse(fit_X.T * fit_X) to use for confidence intervals on predicted values
        # TODO: the existence of this inverse ought to be confirmed before fitting
        # TODO: non-well conditioned matrix often results from failure to standardize X
        self.partial_hat_matrix_ = np.linalg.inv(np.matmul(fit_x.T, fit_x))

        # retain standard error from base model (used for prediction confidence intervals)
        #  TODO : need to determine full RERF degrees of freedom
        base_predicted_y = self.base_regressor_.predict(x_star)
        base_residual_y = y - base_predicted_y
        residual_sum_of_squares = np.sum(base_residual_y ** 2)
        dof = len(x) - len(self.base_regressor_.coef_)
        self.base_regressor_standard_error_ = residual_sum_of_squares / float(dof)

        residual_sum_of_squares = np.sum(y_residuals ** 2)
        self.dof_ = len(x) - len(self.base_regressor_.coef_)
        self.variance_estimate_ = residual_sum_of_squares / float(self.dof_)

        return self

    def _fit_root_regression(self, x, y):
        self.detected_feature_indices_ = []

        # hard wiring which model hyper parameters are used for model optimization
        tunable_hyper_params = {
            SklearnLassoRegressionModelConfig.__name__: {
                'alpha': np.exp([np.log(0.001) + h * (np.log(100) - np.log(0.001)) / 100 for h in range(100)])
            },
            SklearnRidgeRegressionModelConfig.__name__: {
                'alpha': np.exp([np.log(0.001) + h * (np.log(100) - np.log(0.001)) / 100 for h in range(100)])
            }
        }

        if self.model_config.perform_initial_root_model_hyper_parameter_search:
            # tune hyper parameters via k-fold cross validation
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

        else:
            # run lasso with specified params from __init__  or hyper-parameter search
            # fit/refit with original/discovered alpha and X*
            self.base_regressor_ = self.base_regressor_(**self.root_model_kwargs)
            self.base_regressor_.fit(x, y)

            self.screening_root_model_coef_ = self.base_regressor_.coef_

        # ET TODO: capping minimum coef seems to go against the spirit of Lasso/Ridge identifying features
        #  So need to understand if this is needed
        self.detected_feature_indices_ = \
            np.where(np.abs(self.screening_root_model_coef_) >= self.model_config.min_abs_root_model_coef)[0]
        self.base_regressor_.coef_ = self.base_regressor_.coef_[self.detected_feature_indices_]

        # define coef for gradient to polynomial fit
        self._set_polynomial_gradient_coef()

        return self

    def _fit_random_forest_regression(self, x_star, y_residuals):
        if self.model_config.perform_initial_random_forest_hyper_parameter_search:
            num_features = len(x_star[0])
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
            rf_gscv.fit(x_star, y_residuals)

            # retrieve best random forest model and hyper parameters
            self.model_config.random_forest_regressor_ = rf_gscv.best_estimator_

            # only perform hyper-parameter search on first fit
            self.model_config.perform_initial_random_forest_hyper_parameter_search = False

        else:
            self.random_forest_regressor_ = self.random_forest_regressor_(**self.random_forest_kwargs)
            self.random_forest_regressor_.fit(x_star, y_residuals)

        self.random_forest_kwargs = self.random_forest_regressor_.get_params()

        return self

    @trace()
    def predict(self, feature_values_pandas_frame):
        self.logger.info(f"Creating predictions for {len(feature_values_pandas_frame.index)} samples.")

        check_is_fitted(self)

        x = feature_values_pandas_frame[self.input_dimension_names].to_numpy()
        x = check_array(x)

        # if lasso_degree > 1, explode X
        fit_x = self._explode_x(x)

        # restrict to features selected by previous lasso fit
        #   serve as inputs to both regression and random forest on the residuals
        x_star = self._filter_to_detected_features(fit_x)
        y_predicted = self.base_regressor_.predict(x_star) + self.random_forest_regressor_.predict(x_star)

        # compute confidence interval error while preparing return list of Prediction objects
        predictions = []
        target_name = self.output_dimension_names[0]
        for i, xi in enumerate(x):
            leverage_x = np.matmul(np.matmul(xi.T, self.partial_hat_matrix_), xi)

            # split on whether x was in the model fit data
            x_in_fit_x = np.any(np.all(np.isin(x, xi, assume_unique=True), axis=1))
            if x_in_fit_x:
                # return standard error of estimated mean y (from model)
                prediction_var = self.variance_estimate_ * leverage_x
            else:
                # return standard error of extrapolated x
                prediction_var = self.variance_estimate_ * (1.0 + leverage_x)
            predictions.append(
                Prediction(
                    target_name=target_name,
                    mean=y_predicted[i],
                    variance=prediction_var,
                    count=self.dof_)
            )

        return predictions

    def score(self, feature_values_pandas_frame, target_values_pandas_frame):
        x = feature_values_pandas_frame[self.input_dimension_names].to_numpy()
        y = target_values_pandas_frame[self.output_dimension_names].to_numpy()

        y_pred = self.predict(x)
        r2 = r2_score(y, y_pred)
        return r2

    def _explode_x(self, x):
        fit_x = x
        if self.model_config.max_basis_function_degree > 1:
            fit_x = self.polynomial_features_transform_.fit_transform(x)
        return fit_x

    def _filter_to_detected_features(self, fit_x):
        x_star = fit_x[:, self.detected_feature_indices_]
        return x_star

    def _set_polynomial_gradient_coef(self):
        gradient_coef_matrix = []

        fit_coef = self.base_regressor_.coef_  # this skips the intercept term, for which all powers_ values = 0
        fit_poly_powers = self.polynomial_features_transform_.powers_
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
                    p = ip # powers_wrt_xj[i]
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
        fit_x = self._explode_x(x)
        gradient_at_x = np.matmul(fit_x, self.root_model_gradient_coef_)
        return gradient_at_x

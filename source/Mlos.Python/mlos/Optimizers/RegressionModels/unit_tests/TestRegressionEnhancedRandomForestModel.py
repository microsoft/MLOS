#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import unittest

import pandas as pd
import numpy as np
from sklearn.preprocessing import PolynomialFeatures

from mlos.Optimizers.RegressionModels.RegressionEnhancedRandomForestModel import \
    RegressionEnhancedRandomForestRegressionModel, \
    RegressionEnhancedRandomForestRegressionModelConfig

from mlos.Optimizers.RegressionModels.SklearnLassoRegressionModelConfig import SklearnLassoRegressionModelConfig
from mlos.Optimizers.RegressionModels.SklearnRandomForestRegressionModelConfig import\
    SklearnRandomForestRegressionModelConfig

from mlos.Spaces import SimpleHypergrid, ContinuousDimension

import mlos.global_values as global_values
global_values.declare_singletons()


class TestRegressionEnhancedRandomForestRegressionModel(unittest.TestCase):

    def setUp(self):
        # Let's create a simple quadratic response function
        self.input_space = SimpleHypergrid(
            name="2d_X_search_domain",
            dimensions=[
                ContinuousDimension(name="x1", min=0.0, max=5.0),
                ContinuousDimension(name="x2", min=0.0, max=5.0)
            ]
        )
        self.output_space = SimpleHypergrid(
            name="degree2_polynomial",
            dimensions=[
                ContinuousDimension(name="degree2_polynomial_y", min=-10 ** 15, max=10 ** 15)
            ]
        )

        lasso_model_config = SklearnLassoRegressionModelConfig.DEFAULT
        rf_model_config = SklearnRandomForestRegressionModelConfig.DEFAULT
        self.model_config = \
            RegressionEnhancedRandomForestRegressionModelConfig(
                max_basis_function_degree=2,
                min_abs_root_model_coef=0.02,
                boosting_root_model_name=SklearnLassoRegressionModelConfig.__name__,
                boosting_root_model_config=lasso_model_config,
                random_forest_model_config=rf_model_config,
                perform_initial_root_model_hyper_parameter_search=True,
                perform_initial_random_forest_hyper_parameter_search=True)

    @unittest.expectedFailure  # The configs don't belong to their respective config spaces
    def test_lasso_feature_discovery(self):
        rerf = RegressionEnhancedRandomForestRegressionModel(model_config=self.model_config,
                                                             input_space=self.input_space,
                                                             output_space=self.output_space)
        num_x = 100
        np.random.seed(17)
        x = np.random.uniform(0, 5, [num_x, len(self.input_space.dimensions)])
        x_df = pd.DataFrame(x, columns=['x1', 'x2'])

        # y = 1 -3*X_1 -4*X_2 -0.5*X_1**2 -2*X_2**2
        y_coef_true = np.array([1, -3, -4, -0.5, 0.0, -2.0])
        poly_reg = PolynomialFeatures(degree=2)
        poly_terms_x = poly_reg.fit_transform(x)
        y = np.matmul(poly_terms_x, y_coef_true)
        y_df = pd.DataFrame(y, columns=['degree2_polynomial_y'])

        # fit model with same degree as true y
        # rerf = RegressionEnhancedRandomForest(lasso_degree=2)
        rerf.fit(x_df, y_df)

        # test if expected non-zero terms were found
        expected_fit_model_terms = {1, 2, 3, 5}
        expected_symm_diff_found = expected_fit_model_terms - set(rerf.detected_feature_indices_)
        num_diffs = len(list(expected_symm_diff_found))
        assert num_diffs == 0

    @unittest.expectedFailure # The configs don't belong to their respective config spaces
    def test_lasso_coefficients(self):
        rerf = RegressionEnhancedRandomForestRegressionModel(
            model_config=self.model_config,
            input_space=self.input_space,
            output_space=self.output_space
        )
        num_x = 1000
        np.random.seed(23)
        x = np.random.uniform(0, 5, [num_x, len(self.input_space.dimensions)])
        x_df = pd.DataFrame(x, columns=['x1', 'x2'])

        # y = 1 -3*X_1 -4*X_2 -0.5*X_1**2 -2*X_2**2
        y_coef_true = np.array([1, -3, -4, -0.5, 0.0, -2.0])
        poly_reg = PolynomialFeatures(degree=2)
        poly_terms_x = poly_reg.fit_transform(x)
        y = np.matmul(poly_terms_x, y_coef_true)
        y_df = pd.DataFrame(y, columns=['degree2_polynomial_y'])

        # fit model with same degree as true y
        rerf.fit(x_df, y_df)

        # test fit coef match known coef
        epsilon = 10 ** -2
        expected_non_zero_coef = y_coef_true[np.where(y_coef_true != 0.0)[0]]
        fit_poly_coef = [rerf.base_regressor_.intercept_]
        fit_poly_coef.extend(rerf.base_regressor_.coef_)
        incorrect_terms = np.where(np.abs(fit_poly_coef - expected_non_zero_coef) > epsilon)[0]
        num_incorrect_terms = len(incorrect_terms)
        assert num_incorrect_terms == 0

    @unittest.expectedFailure  # The configs don't belong to their respective config spaces
    def test_polynomial_gradient(self):
        rerf = RegressionEnhancedRandomForestRegressionModel(model_config=self.model_config,
                                                             input_space=self.input_space,
                                                             output_space=self.output_space)
        num_x = 100
        np.random.seed(13)
        x = np.random.uniform(0, 5, [num_x, len(self.input_space.dimensions)])
        x_df = pd.DataFrame(x, columns=['x1', 'x2'])

        # y = 1 -3*X_1 -4*X_2 -0.5*X_1**2 -2*X_2**2
        y_coef_true = np.array([1, -3, -4, -0.5, 0.0, -2.0])
        poly_reg = PolynomialFeatures(degree=2)
        poly_terms_x = poly_reg.fit_transform(x)
        y = np.matmul(poly_terms_x, y_coef_true)
        y_df = pd.DataFrame(y, columns=['degree2_polynomial_y'])

        # fit model with same degree as true y
        rerf.fit(x_df, y_df)

        # test gradient at X
        epsilon = 10 ** -2
        true_gradient_coef = np.array([[-3, -0.5 * 2, 0, 0, 0, 0], [-4, -2.0 * 2, 0, 0, 0, 0]]).transpose()
        incorrect_terms = np.where(np.abs(true_gradient_coef - rerf.root_model_gradient_coef_) > epsilon)[0]
        num_incorrect_terms = len(incorrect_terms)
        assert num_incorrect_terms == 0

#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import unittest

import math
import pandas as pd
import numpy as np
from sklearn.preprocessing import PolynomialFeatures

from mlos.Optimizers.RegressionModels.Prediction import Prediction
from mlos.Optimizers.RegressionModels.RegressionEnhancedRandomForestModel import \
    RegressionEnhancedRandomForestRegressionModel, \
    RegressionEnhancedRandomForestRegressionModelConfig
from mlos.Optimizers.RegressionModels.SklearnLassoRegressionModelConfig import SklearnLassoRegressionModelConfig
from mlos.Optimizers.RegressionModels.SklearnRandomForestRegressionModelConfig import SklearnRandomForestRegressionModelConfig
from mlos.Spaces import SimpleHypergrid, ContinuousDimension, CategoricalDimension
from mlos.SynthethicFunctions.HierarchicalFunctions import MultilevelQuadratic
import mlos.global_values as global_values


class TestRegressionEnhancedRandomForestRegressionModel(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        global_values.declare_singletons()

    def setUp(self):
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

        self.test_case_globals = {
            '2d_X_input_space': SimpleHypergrid(
                name="2d_X_search_domain",
                dimensions=[
                    ContinuousDimension(name="x1", min=0.0, max=5.0),
                    ContinuousDimension(name="x2", min=0.0, max=5.0)
                ]
            ),
            'categorical_input_space': SimpleHypergrid(
                name="categorical_search_domain",
                dimensions=[
                    CategoricalDimension(name='x0', values=['a', 'b', 'c']),
                    ContinuousDimension(name="x1", min=0.0, max=5.0),
                    ContinuousDimension(name="x2", min=0.0, max=5.0),
                    CategoricalDimension(name='i0', values=['-5', '5'])
                ]
            ),
            'categorical_hierarchical_input_space': SimpleHypergrid(
                name="categorical_search_domain",
                dimensions=[
                    CategoricalDimension(name='x0', values=['a', 'b', 'c']),
                    ContinuousDimension(name="x1", min=0.0, max=5.0),
                    ContinuousDimension(name="x2", min=0.0, max=5.0),
                    CategoricalDimension(name='i0', values=['-5', '5'])
                ]
            ),
            'output_space': SimpleHypergrid(
                name="degree2_polynomial",
                dimensions=[
                    ContinuousDimension(name="degree2_polynomial_y", min=-10 ** 15, max=10 ** 15)
                ]
            )
        }

    @staticmethod
    def n_choose_k(n, k):
        return math.factorial(n) / math.factorial(k) / math.factorial(n - k)

    @staticmethod
    def get_simple_quadratic_coefficients():
        return np.array([1, -3, -4, -0.5, 0.0, -2.0])

    @staticmethod
    def generate_points_simple_quadratic(num_points, num_features):
        x = np.random.uniform(0, 5, [num_points, num_features])
        x_df = pd.DataFrame(x, columns=['x1', 'x2'])

        # y = 1 -3*X_1 -4*X_2 -0.5*X_1**2 -2*X_2**2
        y_coef_true = TestRegressionEnhancedRandomForestRegressionModel.get_simple_quadratic_coefficients()
        poly_reg = PolynomialFeatures(degree=2)
        poly_terms_x = poly_reg.fit_transform(x)
        y = np.matmul(poly_terms_x, y_coef_true)
        y_df = pd.DataFrame(y, columns=['degree2_polynomial_y'])
        return x_df, y_df

    @staticmethod
    def generate_points_nonhierarchical_categorical_quadratic(num_points):
        # evaluate y at the random x created above
        model_params = {
            'a': [10, 3, 7, 0, 0, 0],
            'b': [20, 3, -4, 0, 12, 0],
            'c': [30, 0, 0, 2, 0, 3]
        }

        x_df = pd.DataFrame({
            'x0': np.random.choice(['a', 'b', 'c'], size=num_points),
            'x1': np.random.uniform(-10, 10, size=num_points),
            'x2': np.random.uniform(-10, 10, size=num_points),
            'i0': np.random.choice(['-5', '5'], size=num_points)
        })

        y_poly_feature = PolynomialFeatures(degree=2)
        for x0 in x_df['x0'].unique():
            x0_slice = x_df.loc[x_df['x0'] == x0, ['x1', 'x2']]
            x_basis = y_poly_feature.fit_transform(x0_slice.to_numpy())
            x_df.loc[x0_slice.index, 'degree2_polynomial_y'] = np.matmul(x_basis, model_params[x0])
            if x0 == 'c':
                x_df.loc[x0_slice.index, 'degree2_polynomial_y'] += x_df['i0'].astype(float)
        y_df = pd.DataFrame(x_df['degree2_polynomial_y'])
        x_df.drop(columns=['degree2_polynomial_y'], inplace=True)

        return x_df, y_df

    # @unittest.expectedFailure  # The configs don't belong to their respective config spaces
    def test_lasso_feature_discovery(self):
        rerf = RegressionEnhancedRandomForestRegressionModel(
            model_config=self.model_config,
            input_space=self.test_case_globals['2d_X_input_space'],
            output_space=self.test_case_globals['output_space']
        )

        np.random.seed(17)
        num_points = 100
        x_df, y_df = self.generate_points_simple_quadratic(num_points, len(self.test_case_globals['2d_X_input_space'].dimensions))
        rerf.fit(x_df, y_df)

        final_num_features = 2
        polynomial_degree = self.model_config.max_basis_function_degree
        num_terms_in_polynomial = self.n_choose_k(polynomial_degree + final_num_features, final_num_features)

        self.assertTrue(rerf.root_model_gradient_coef_.shape == (num_terms_in_polynomial, final_num_features), 'Gradient coefficient shape is incorrect')
        self.assertTrue(rerf.fit_X_.shape == (num_points, num_terms_in_polynomial), 'Design matrix shape is incorrect')
        self.assertTrue(rerf.partial_hat_matrix_.shape == (num_terms_in_polynomial, num_terms_in_polynomial), 'Hat matrix shape is incorrect')
        self.assertTrue(rerf.polynomial_features_powers_.shape == (num_terms_in_polynomial, final_num_features), 'PolynomalFeature.power_ shape is incorrect')

        # test if expected non-zero terms were found
        expected_fit_model_terms = {1, 2, 3, 5}
        expected_symm_diff_found = expected_fit_model_terms - set(rerf.detected_feature_indices_)
        num_diffs = len(list(expected_symm_diff_found))
        self.assertTrue(num_diffs == 0, 'Base model failed to find expected features')

    # @unittest.expectedFailure # The configs don't belong to their respective config spaces
    def test_lasso_polynomial_coefficients(self):
        rerf = RegressionEnhancedRandomForestRegressionModel(
            model_config=self.model_config,
            input_space=self.test_case_globals['2d_X_input_space'],
            output_space=self.test_case_globals['output_space']
        )

        np.random.seed(23)
        num_points = 1000
        x_df, y_df = self.generate_points_simple_quadratic(num_points, len(self.test_case_globals['2d_X_input_space'].dimensions))
        rerf.fit(x_df, y_df)

        final_num_features = 2
        polynomial_degree = self.model_config.max_basis_function_degree
        num_terms_in_polynomial = self.n_choose_k(polynomial_degree + final_num_features, final_num_features)

        self.assertTrue(rerf.root_model_gradient_coef_.shape == (num_terms_in_polynomial, final_num_features), 'Gradient coefficient shape is incorrect')
        self.assertTrue(rerf.fit_X_.shape == (num_points, num_terms_in_polynomial), 'Design matrix shape is incorrect')
        self.assertTrue(rerf.partial_hat_matrix_.shape == (num_terms_in_polynomial, num_terms_in_polynomial), 'Hat matrix shape is incorrect')
        self.assertTrue(rerf.polynomial_features_powers_.shape == (num_terms_in_polynomial, final_num_features), 'PolynomalFeature.power_ shape is incorrect')

        # test fit coef match known coef
        y_coef_true = self.get_simple_quadratic_coefficients()
        epsilon = 10 ** -2
        expected_non_zero_coef = y_coef_true[np.where(y_coef_true != 0.0)[0]]
        fit_poly_coef = [rerf.base_regressor_.intercept_]
        fit_poly_coef.extend(rerf.base_regressor_.coef_)
        incorrect_terms = np.where(np.abs(fit_poly_coef - expected_non_zero_coef) > epsilon)[0]
        num_incorrect_terms = len(incorrect_terms)
        self.assertTrue(num_incorrect_terms == 0, 'Estimated polynomial coefficients deviated further than expected from known coefficients')

    # @unittest.expectedFailure  # The configs don't belong to their respective config spaces
    def test_lasso_polynomial_gradient(self):
        rerf = RegressionEnhancedRandomForestRegressionModel(
            model_config=self.model_config,
            input_space=self.test_case_globals['2d_X_input_space'],
            output_space=self.test_case_globals['output_space']
        )

        np.random.seed(13)
        num_points = 100
        x_df, y_df = self.generate_points_simple_quadratic(num_points, len(self.test_case_globals['2d_X_input_space'].dimensions))
        rerf.fit(x_df, y_df)

        final_num_features = 2
        polynomial_degree = self.model_config.max_basis_function_degree
        num_terms_in_polynomial = self.n_choose_k(polynomial_degree + final_num_features, final_num_features)

        self.assertTrue(rerf.root_model_gradient_coef_.shape == (num_terms_in_polynomial, final_num_features), 'Gradient coefficient shape is incorrect')
        self.assertTrue(rerf.fit_X_.shape == (num_points, num_terms_in_polynomial), 'Design matrix shape is incorrect')
        self.assertTrue(rerf.partial_hat_matrix_.shape == (num_terms_in_polynomial, num_terms_in_polynomial), 'Hat matrix shape is incorrect')
        self.assertTrue(rerf.polynomial_features_powers_.shape == (num_terms_in_polynomial, final_num_features), 'PolynomalFeature.power_ shape is incorrect')

        # test gradient at X
        epsilon = 10 ** -2
        true_gradient_coef = np.array([[-3, -0.5 * 2, 0, 0, 0, 0], [-4, -2.0 * 2, 0, 0, 0, 0]]).transpose()
        incorrect_terms = np.where(np.abs(true_gradient_coef - rerf.root_model_gradient_coef_) > epsilon)[0]
        num_incorrect_terms = len(incorrect_terms)
        self.assertTrue(num_incorrect_terms == 0, 'Estimated gradient coefficients deviated further than expected from known coefficients')

    # @unittest.expectedFailure  # The configs don't belong to their respective config spaces
    def test_lasso_predictions(self):
        rerf = RegressionEnhancedRandomForestRegressionModel(
            model_config=self.model_config,
            input_space=self.test_case_globals['2d_X_input_space'],
            output_space=self.test_case_globals['output_space']
        )
        np.random.seed(13)

        num_train_points = 100
        x_train_df, y_train_df = self.generate_points_simple_quadratic(num_train_points, len(self.test_case_globals['2d_X_input_space'].dimensions))
        rerf.fit(x_train_df, y_train_df)

        final_num_features = 2
        polynomial_degree = self.model_config.max_basis_function_degree
        num_terms_in_polynomial = self.n_choose_k(polynomial_degree + final_num_features, final_num_features)

        self.assertTrue(rerf.root_model_gradient_coef_.shape == (num_terms_in_polynomial, final_num_features), 'Gradient coefficient shape is incorrect')
        self.assertTrue(rerf.fit_X_.shape == (num_train_points, num_terms_in_polynomial), 'Design matrix shape is incorrect')
        self.assertTrue(rerf.partial_hat_matrix_.shape == (num_terms_in_polynomial, num_terms_in_polynomial), 'Hat matrix shape is incorrect')
        self.assertTrue(rerf.polynomial_features_powers_.shape == (num_terms_in_polynomial, final_num_features), 'PolynomalFeature.power_ shape is incorrect')

        # generate new random sample to test predictions
        num_test_points = 50
        x_test_df, y_test_df = self.generate_points_simple_quadratic(num_test_points, len(self.test_case_globals['2d_X_input_space'].dimensions))
        predictions = rerf.predict(x_test_df)
        pred_df = predictions.get_dataframe()

        predicted_value_col = Prediction.LegalColumnNames.PREDICTED_VALUE.value
        predicted_y = pred_df[predicted_value_col].to_numpy()
        y_test = y_test_df.to_numpy().reshape(-1)
        residual_sum_of_squares = ((y_test - predicted_y) ** 2).sum()
        total_sum_of_squares = ((y_test - y_test.mean()) ** 2).sum()
        r2 = 1 - residual_sum_of_squares / total_sum_of_squares

        self.assertTrue(r2 > 1 - 10**-4, '1 - R^2 larger than expected')

    def test_lasso_categorical_predictions(self):
        rerf = RegressionEnhancedRandomForestRegressionModel(
            model_config=self.model_config,
            input_space=self.test_case_globals['categorical_input_space'],
            output_space=self.test_case_globals['output_space']
        )

        num_train_x = 300
        x_train_df, y_train_df = self.generate_points_nonhierarchical_categorical_quadratic(num_train_x)
        rerf.fit(x_train_df, y_train_df)

        num_categorical_levels_expected = len(x_train_df['x0'].unique()) * len(x_train_df['i0'].unique())
        num_continuous_dimensions = 2  # x1 and x2
        final_num_features = num_categorical_levels_expected - 1 + num_continuous_dimensions
        polynomial_degree = self.model_config.max_basis_function_degree
        num_terms_in_polynomial_per_categorical_level = self.n_choose_k(polynomial_degree + num_continuous_dimensions, num_continuous_dimensions)
        num_terms_in_polynomial = num_terms_in_polynomial_per_categorical_level * num_categorical_levels_expected

        self.assertTrue(rerf.root_model_gradient_coef_.shape == (num_terms_in_polynomial, final_num_features), 'Gradient coefficient shape is incorrect')
        self.assertTrue(rerf.fit_X_.shape == (num_train_x, num_terms_in_polynomial), 'Design matrix shape is incorrect')
        self.assertTrue(rerf.partial_hat_matrix_.shape == (num_terms_in_polynomial, num_terms_in_polynomial), 'Hat matrix shape is incorrect')
        self.assertTrue(rerf.polynomial_features_powers_.shape == (num_terms_in_polynomial, final_num_features), 'PolynomalFeature.power_ shape is incorrect')

        # generate new random to test predictions
        num_test_points = 50
        x_test_df, y_test_df = self.generate_points_nonhierarchical_categorical_quadratic(num_test_points)

        predictions = rerf.predict(x_test_df)
        pred_df = predictions.get_dataframe()

        predicted_value_col = Prediction.LegalColumnNames.PREDICTED_VALUE.value
        predicted_y = pred_df[predicted_value_col].to_numpy()
        y_test = y_test_df.to_numpy().reshape(-1)
        residual_sum_of_squares = ((y_test - predicted_y) ** 2).sum()
        total_sum_of_squares = ((y_test - y_test.mean()) ** 2).sum()
        unexplained_variance = residual_sum_of_squares / total_sum_of_squares
        self.assertTrue(unexplained_variance < 10 ** -4, '1 - R^2 larger than expected')

    def test_lasso_categorical_gradient(self):
        rerf = RegressionEnhancedRandomForestRegressionModel(
            model_config=self.model_config,
            input_space=self.test_case_globals['categorical_input_space'],
            output_space=self.test_case_globals['output_space']
        )
        np.random.seed(19)

        num_points = 300
        x_df, y_df = self.generate_points_nonhierarchical_categorical_quadratic(num_points)
        rerf.fit(x_df, y_df)

        num_categorical_levels_expected = len(x_df['x0'].unique()) * len(x_df['i0'].unique())
        num_continuous_dimensions = 2  # x1 and x2
        final_num_features = num_categorical_levels_expected - 1 + num_continuous_dimensions
        polynomial_degree = self.model_config.max_basis_function_degree
        num_terms_in_polynomial_per_categorical_level = self.n_choose_k(polynomial_degree + num_continuous_dimensions, num_continuous_dimensions)
        num_terms_in_polynomial = num_terms_in_polynomial_per_categorical_level * num_categorical_levels_expected

        self.assertTrue(rerf.root_model_gradient_coef_.shape == (num_terms_in_polynomial, final_num_features), 'Gradient coefficient shape is incorrect')
        self.assertTrue(rerf.fit_X_.shape == (num_points, num_terms_in_polynomial), 'Design matrix shape is incorrect')
        self.assertTrue(rerf.partial_hat_matrix_.shape == (num_terms_in_polynomial, num_terms_in_polynomial), 'Hat matrix shape is incorrect')
        self.assertTrue(rerf.polynomial_features_powers_.shape == (num_terms_in_polynomial, final_num_features), 'PolynomalFeature.power_ shape is incorrect')

        # test gradient coefficients
        true_gradient_coef = np.zeros((36, 7))
        true_gradient_coef[0] = np.array([3, 7, 0, 10, 10, 15, 25])
        true_gradient_coef[1] = np.array([12, -11, 0, -11, -11, -3, -3])
        true_gradient_coef[11] = np.array([12, 12, 0, 12, 12, -7, -7])
        true_gradient_coef[13] = np.array([-3, -11, 0, 0, 0, 2, 2])
        true_gradient_coef[15] = np.array([4, 12, 0, 0, 0, 3, 3])
        true_gradient_coef[17] = np.array([-3, -7, 0, 0, 0, 0, 0])
        true_gradient_coef[19] = np.array([4, 6, 0, 0, 0, 0, 0])
        true_gradient_coef[21] = np.array([0, -7, 0, 0, 0, 0, 0])
        true_gradient_coef[23] = np.array([0, 6, 0, 0, 0, 0, 0])

        epsilon = 10 ** -2
        estimated_gradient_coef = rerf.root_model_gradient_coef_
        coef_abs_diff = np.abs(true_gradient_coef - estimated_gradient_coef)
        coef_abs_relative_error = np.divide(coef_abs_diff, np.abs(true_gradient_coef))
        incorrect_terms = np.where(coef_abs_relative_error > epsilon)[0]
        num_incorrect_terms = len(incorrect_terms)

        self.assertTrue(num_incorrect_terms == 0, 'Estimated gradient coefficients deviated further than expected from known coefficients')

    def test_lasso_hierarchical_categorical_predictions(self):
        this_tests_input_space = MultilevelQuadratic.CONFIG_SPACE
        rerf = RegressionEnhancedRandomForestRegressionModel(
            model_config=self.model_config,
            input_space=this_tests_input_space,
            output_space=self.test_case_globals['output_space']
        )

        def generate_points(num_points):
            x_list = []
            output_dim_name = self.test_case_globals['output_space'].dimensions[0].name
            y_dict = {output_dim_name: []}
            for _ in range(num_points):
                xi = this_tests_input_space.random()
                yi = MultilevelQuadratic.evaluate(xi)
                xi_df = pd.DataFrame({
                    param_name: [param_value]
                    for param_name, param_value in xi
                })
                x_list.append(xi_df)
                y_dict[output_dim_name].append(yi)
            x_df = pd.concat(x_list).reset_index(drop=True)
            y_df = pd.DataFrame(y_dict)
            return x_df, y_df

        # fit model with same degree as true y
        num_train_x = 100
        x_train_df, y_train_df = generate_points(num_train_x)
        rerf.fit(x_train_df, y_train_df)

        self.assertTrue(rerf.root_model_gradient_coef_.shape == (28, 8), 'Gradient coefficient shape is incorrect')
        self.assertTrue(rerf.fit_X_.shape == (num_train_x, 28), 'Design matrix shape is incorrect')
        self.assertTrue(rerf.partial_hat_matrix_.shape == (28, 28), 'Hat matrix shape is incorrect')
        self.assertTrue(rerf.polynomial_features_powers_.shape == (28, 8), 'PolynomalFeature.power_ shape is incorrect')

        # test predictions
        num_test_x = 10
        x_test_df, y_test_df = generate_points(num_test_x)

        predictions = rerf.predict(x_test_df)
        pred_df = predictions.get_dataframe()

        predicted_value_col = Prediction.LegalColumnNames.PREDICTED_VALUE.value
        predicted_y = pred_df[predicted_value_col].to_numpy()
        y_test = y_test_df.to_numpy().reshape(-1)
        residual_sum_of_squares = ((y_test - predicted_y) ** 2).sum()
        total_sum_of_squares = ((y_test - y_test.mean()) ** 2).sum()
        unexplained_variance = residual_sum_of_squares / total_sum_of_squares
        self.assertTrue(unexplained_variance < 10**-4, '1 - R^2 larger than expected')

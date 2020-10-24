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
from mlos.Spaces import SimpleHypergrid, ContinuousDimension, CategoricalDimension
from mlos.OptimizerEvaluationTools.ObjectiveFunctionFactory import ObjectiveFunctionFactory, objective_function_config_store
import mlos.global_values as global_values


class TestRegressionEnhancedRandomForestRegressionModel(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        global_values.declare_singletons()

    def setUp(self):
        self.model_config = RegressionEnhancedRandomForestRegressionModelConfig.DEFAULT

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
        num_detected_features = len(rerf.detected_feature_indices_)

        self.assertTrue(rerf.polynomial_features_powers_.shape == (num_terms_in_polynomial, final_num_features), 'PolynomalFeature.power_ shape is incorrect')
        self.assertTrue(rerf.root_model_gradient_coef_.shape == rerf.polynomial_features_powers_.shape, 'Gradient coefficient shape is incorrect')
        self.assertTrue(rerf.fit_X_.shape == (num_points, num_terms_in_polynomial), 'Design matrix shape is incorrect')
        self.assertTrue(rerf.partial_hat_matrix_.shape == (num_detected_features, num_detected_features), 'Hat matrix shape is incorrect')

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
        num_detected_features = len(rerf.detected_feature_indices_)

        self.assertTrue(rerf.polynomial_features_powers_.shape == (num_terms_in_polynomial, final_num_features), 'PolynomalFeature.power_ shape is incorrect')
        self.assertTrue(rerf.root_model_gradient_coef_.shape == rerf.polynomial_features_powers_.shape, 'Gradient coefficient shape is incorrect')
        self.assertTrue(rerf.fit_X_.shape == (num_points, num_terms_in_polynomial), 'Design matrix shape is incorrect')
        self.assertTrue(rerf.partial_hat_matrix_.shape == (num_detected_features, num_detected_features), 'Hat matrix shape is incorrect')

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
        num_detected_features = len(rerf.detected_feature_indices_)

        self.assertTrue(rerf.polynomial_features_powers_.shape == (num_terms_in_polynomial, final_num_features), 'PolynomalFeature.power_ shape is incorrect')
        self.assertTrue(rerf.root_model_gradient_coef_.shape == rerf.polynomial_features_powers_.shape, 'Gradient coefficient shape is incorrect')
        self.assertTrue(rerf.fit_X_.shape == (num_points, num_terms_in_polynomial), 'Design matrix shape is incorrect')
        self.assertTrue(rerf.partial_hat_matrix_.shape == (num_detected_features, num_detected_features), 'Hat matrix shape is incorrect')

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
        num_detected_features = len(rerf.detected_feature_indices_)

        self.assertTrue(rerf.polynomial_features_powers_.shape == (num_terms_in_polynomial, final_num_features), 'PolynomalFeature.power_ shape is incorrect')
        self.assertTrue(rerf.root_model_gradient_coef_.shape == rerf.polynomial_features_powers_.shape, 'Gradient coefficient shape is incorrect')
        self.assertTrue(rerf.fit_X_.shape == (num_train_points, num_terms_in_polynomial), 'Design matrix shape is incorrect')
        self.assertTrue(rerf.partial_hat_matrix_.shape == (num_detected_features, num_detected_features), 'Hat matrix shape is incorrect')

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

        num_categorical_levels_expected = len(rerf.one_hot_encoder_adapter.get_one_hot_encoded_column_names())
        num_continuous_dimensions = 2  # x1 and x2
        final_num_features = num_categorical_levels_expected + num_continuous_dimensions
        polynomial_degree = self.model_config.max_basis_function_degree
        num_terms_in_polynomial_per_categorical_level = self.n_choose_k(polynomial_degree + num_continuous_dimensions, num_continuous_dimensions)
        num_terms_in_polynomial = num_terms_in_polynomial_per_categorical_level * (num_categorical_levels_expected + 1)\
                                  - len(rerf.categorical_zero_cols_idx_to_delete_)
        num_detected_features = len(rerf.detected_feature_indices_)

        self.assertTrue(rerf.root_model_gradient_coef_.shape == rerf.polynomial_features_powers_.shape, 'Gradient coefficient shape is incorrect')
        self.assertTrue(rerf.fit_X_.shape == (num_train_x, num_terms_in_polynomial), 'Design matrix shape is incorrect')
        self.assertTrue(rerf.partial_hat_matrix_.shape == (num_detected_features, num_detected_features), 'Hat matrix shape is incorrect')
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

        num_categorical_levels_expected = len(rerf.one_hot_encoder_adapter.get_one_hot_encoded_column_names())
        num_continuous_dimensions = 2  # x1 and x2
        final_num_features = num_categorical_levels_expected + num_continuous_dimensions
        polynomial_degree = self.model_config.max_basis_function_degree
        num_terms_in_polynomial_per_categorical_level = self.n_choose_k(polynomial_degree + num_continuous_dimensions, num_continuous_dimensions)
        num_terms_in_polynomial = num_terms_in_polynomial_per_categorical_level * (num_categorical_levels_expected + 1)\
                                  - len(rerf.categorical_zero_cols_idx_to_delete_)
        num_detected_features = len(rerf.detected_feature_indices_)

        self.assertTrue(rerf.root_model_gradient_coef_.shape == rerf.polynomial_features_powers_.shape, 'Gradient coefficient shape is incorrect')
        self.assertTrue(rerf.fit_X_.shape == (num_points, num_terms_in_polynomial), 'Design matrix shape is incorrect')
        self.assertTrue(rerf.partial_hat_matrix_.shape == (num_detected_features, num_detected_features), 'Hat matrix shape is incorrect')
        self.assertTrue(rerf.polynomial_features_powers_.shape == (num_terms_in_polynomial, final_num_features), 'PolynomalFeature.power_ shape is incorrect')

        # test gradient coefficients
        print(rerf.root_model_gradient_coef_.shape)
        print(rerf.root_model_gradient_coef_)
        true_gradient_coef = np.zeros((42, 13))
        # true_gradient_coef[0:21, :] = np.array([
        #     [-0.88923257, -1.80685348, 0, 0, 0, -37.95940666, -37.95680438, 0, -27.96056314, -27.96181644, 0, -22.95675436, -12.95597631],
        #     [1.64393929, 5.39040704, 0, 0, 0, 7.88887524, 7.88906753, 0, -3.11034223, -3.11049021, 0, 0.88860922, 0.88915106],
        #     [5.39040704, 1.26819354, 0, 0, 0, 4.80646378, 4.8065159, 0,   4.80727136, 4.80677374, 0, 1.80669593, 1.80646945],
        #     [7.88887524, 4.80646378, 0, 0, 0, -0.82209434, -0.82215961, 0, -0.82206655, -0.8220557, 0, 2.17795658, 2.17784683],
        #     [-1.64418868, -5.39041784, 0, 0, 0, -5.39041784, -5.39038081, 0,   6.60961819, 6.60959012, 0, -5.39038292, -5.39040983],
        #     [-5.39041784, -1.26836587, 0, 0, 0, -0.63418294, -0.63419727, 0, -0.63409985, -0.63410744, 0, 1.36580166, 1.36585864],
        #     [7.88906753, 4.8065159, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.],
        #     [-1.64431922, -5.39038081, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.],
        #     [-5.39038081, -1.26839454, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.],
        #     [-3.11034223, 4.80727136, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.],
        #     [-1.6441331, 6.60961819, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.],
        #     [6.60961819, -1.26819971, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.],
        #     [-3.11049021, 4.80677374, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.],
        #     [-1.6441114, 6.60959012, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.],
        #     [6.60959012, -1.26821488, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.],
        #     [0.88860922, 1.80669593, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.],
        #     [4.35591316, -5.39038292, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.],
        #     [-5.39038292, 2.73160333, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.],
        #     [0.88915106, 1.80646945, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.],
        #     [4.35569365, -5.39040983, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.],
        #     [-5.39040983, 2.73171727, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.]
        # ])
        true_gradient_coef[0:21, :] = np.array([
            [-1, -2, 0, 0, 0, -38, -38, 0, -28, -28, 0, -23, -13],
            [2, 5, 0, 0, 0, 8, 8, 0, -3, -3, 0, 1, 1],
            [5, 1, 0, 0, 0, 5, 5, 0, 5, 5, 0, 2, 2],
            [8, 5, 0, 0, 0, -1, -1, 0, -1, -1, 0, 2, 2],
            [-2, -5, 0, 0, 0, -5, -5, 0, 7, 7, 0, -5, -5],
            [-5, -1, 0, 0, 0, -1, -1, 0, -1, -1, 0, 1, 1],
            [8, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.],
            [-2, -5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.],
            [-5, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.],
            [-3, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.],
            [-2, 7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.],
            [7, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.],
            [-3, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.],
            [-2, 7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.],
            [7, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.],
            [1, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.],
            [4, -5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.],
            [-5, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.],
            [1, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.],
            [4, -5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.],
            [-5, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.]
        ])

        epsilon = 10 ** -2
        estimated_gradient_coef = rerf.root_model_gradient_coef_
        coef_abs_diff = np.abs(true_gradient_coef - estimated_gradient_coef)
        coef_abs_relative_error = np.divide(coef_abs_diff, np.abs(true_gradient_coef))
        print(coef_abs_relative_error)
        incorrect_terms = np.where(coef_abs_relative_error > epsilon)[0]
        num_incorrect_terms = len(incorrect_terms)

        self.assertTrue(num_incorrect_terms == 0, 'Estimated gradient coefficients deviated further than expected from known coefficients')

    def test_lasso_hierarchical_categorical_predictions(self):
        objective_function_config = objective_function_config_store.get_config_by_name('three_level_quadratic')
        objective_function = ObjectiveFunctionFactory.create_objective_function(objective_function_config=objective_function_config)


        rerf = RegressionEnhancedRandomForestRegressionModel(
            model_config=self.model_config,
            input_space=objective_function.parameter_space,
            output_space=objective_function.output_space
        )

        # fit model with same degree as true y
        num_train_x = 100
        x_train_df = objective_function.parameter_space.random_dataframe(num_samples=num_train_x)
        y_train_df = objective_function.evaluate_dataframe(x_train_df)
        rerf.fit(x_train_df, y_train_df)
        num_detected_features = len(rerf.detected_feature_indices_)

        self.assertTrue(rerf.root_model_gradient_coef_.shape == rerf.polynomial_features_powers_.shape, 'Gradient coefficient shape is incorrect')
        self.assertTrue(rerf.fit_X_.shape == (num_train_x, rerf.polynomial_features_powers_.shape[0]), 'Design matrix shape is incorrect')
        self.assertTrue(rerf.partial_hat_matrix_.shape == (num_detected_features, num_detected_features), 'Hat matrix shape is incorrect')
        self.assertTrue(rerf.polynomial_features_powers_.shape == (34, 9), 'PolynomalFeature.power_ shape is incorrect')

        # test predictions
        predicted_value_col = Prediction.LegalColumnNames.PREDICTED_VALUE.value
        num_test_x = 10

        # by generating a single X feature on which to make the predictions, the
        y_test_list = []
        predicted_y_list = []
        for _ in range(num_test_x):
            x_test_df = objective_function.parameter_space.random_dataframe(num_samples=1)
            y_test_df = objective_function.evaluate_dataframe(x_test_df)
            y_test_list.append(y_test_df['y'].values[0])

            predictions = rerf.predict(x_test_df)
            pred_df = predictions.get_dataframe()
            predicted_y_list.append(pred_df[predicted_value_col].values[0])

        predicted_y = np.array(predicted_y_list)
        y_test = np.array(y_test_list)
        residual_sum_of_squares = ((y_test - predicted_y) ** 2).sum()
        total_sum_of_squares = ((y_test - y_test.mean()) ** 2).sum()
        unexplained_variance = residual_sum_of_squares / total_sum_of_squares
        self.assertTrue(unexplained_variance < 10**-4, '1 - R^2 larger than expected')

#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import random
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


class TestRegressionEnhancedRandomForestRegressionModel:

    @classmethod
    def setup_class(cls):
        global_values.declare_singletons()

    def setup_method(self, method):
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
            'x1': np.random.uniform(0, 5, size=num_points),
            'x2': np.random.uniform(0, 5, size=num_points),
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

        num_points = 100
        x_df, y_df = self.generate_points_simple_quadratic(num_points, len(self.test_case_globals['2d_X_input_space'].dimensions))
        rerf.fit(x_df, y_df)

        final_num_features = 2
        polynomial_degree = self.model_config.max_basis_function_degree
        num_terms_in_polynomial = self.n_choose_k(polynomial_degree + final_num_features, final_num_features)
        num_detected_features = len(rerf.detected_feature_indices_)

        assert rerf.polynomial_features_powers_.shape == (num_terms_in_polynomial, final_num_features), 'PolynomalFeature.power_ shape is incorrect'
        assert rerf.root_model_gradient_coef_.shape == rerf.polynomial_features_powers_.shape, 'Gradient coefficient shape is incorrect'
        assert rerf.fit_X_.shape == (num_points, num_terms_in_polynomial), 'Design matrix shape is incorrect'
        assert rerf.partial_hat_matrix_.shape == (num_detected_features, num_detected_features), 'Hat matrix shape is incorrect'

        # test if expected non-zero terms were found
        expected_fit_model_terms = {1, 2, 3, 5}
        expected_symm_diff_found = expected_fit_model_terms - set(rerf.detected_feature_indices_)
        num_diffs = len(list(expected_symm_diff_found))
        assert num_diffs == 0, 'Base model failed to find expected features'

    # @unittest.expectedFailure # The configs don't belong to their respective config spaces
    def test_lasso_polynomial_coefficient_invariants(self):
        rerf = RegressionEnhancedRandomForestRegressionModel(
            model_config=self.model_config,
            input_space=self.test_case_globals['2d_X_input_space'],
            output_space=self.test_case_globals['output_space']
        )

        num_points = 100
        x_df, y_df = self.generate_points_simple_quadratic(num_points, len(self.test_case_globals['2d_X_input_space'].dimensions))
        rerf.fit(x_df, y_df)

        final_num_features = 2
        polynomial_degree = self.model_config.max_basis_function_degree
        num_terms_in_polynomial = self.n_choose_k(polynomial_degree + final_num_features, final_num_features)
        num_detected_features = len(rerf.detected_feature_indices_)

        assert rerf.polynomial_features_powers_.shape == (num_terms_in_polynomial, final_num_features), 'PolynomalFeature.power_ shape is incorrect'
        assert rerf.root_model_gradient_coef_.shape == rerf.polynomial_features_powers_.shape, 'Gradient coefficient shape is incorrect'
        assert rerf.fit_X_.shape == (num_points, num_terms_in_polynomial), 'Design matrix shape is incorrect'
        assert rerf.partial_hat_matrix_.shape == (num_detected_features, num_detected_features), 'Hat matrix shape is incorrect'

    # @unittest.expectedFailure  # The configs don't belong to their respective config spaces
    def test_lasso_polynomial_gradient_invariants(self):
        rerf = RegressionEnhancedRandomForestRegressionModel(
            model_config=self.model_config,
            input_space=self.test_case_globals['2d_X_input_space'],
            output_space=self.test_case_globals['output_space']
        )

        num_points = 100
        x_df, y_df = self.generate_points_simple_quadratic(num_points, len(self.test_case_globals['2d_X_input_space'].dimensions))
        rerf.fit(x_df, y_df)

        final_num_features = 2
        polynomial_degree = self.model_config.max_basis_function_degree
        num_terms_in_polynomial = self.n_choose_k(polynomial_degree + final_num_features, final_num_features)
        num_detected_features = len(rerf.detected_feature_indices_)

        assert rerf.polynomial_features_powers_.shape == (num_terms_in_polynomial, final_num_features), 'PolynomalFeature.power_ shape is incorrect'
        assert rerf.root_model_gradient_coef_.shape == rerf.polynomial_features_powers_.shape, 'Gradient coefficient shape is incorrect'
        assert rerf.fit_X_.shape == (num_points, num_terms_in_polynomial), 'Design matrix shape is incorrect'
        assert rerf.partial_hat_matrix_.shape == (num_detected_features, num_detected_features), 'Hat matrix shape is incorrect'

    # @unittest.expectedFailure  # The configs don't belong to their respective config spaces
    def test_lasso_predictions(self):
        rerf = RegressionEnhancedRandomForestRegressionModel(
            model_config=self.model_config,
            input_space=self.test_case_globals['2d_X_input_space'],
            output_space=self.test_case_globals['output_space']
        )

        num_train_points = 100
        x_train_df, y_train_df = self.generate_points_simple_quadratic(num_train_points, len(self.test_case_globals['2d_X_input_space'].dimensions))
        rerf.fit(x_train_df, y_train_df)

        final_num_features = 2
        polynomial_degree = self.model_config.max_basis_function_degree
        num_terms_in_polynomial = self.n_choose_k(polynomial_degree + final_num_features, final_num_features)
        num_detected_features = len(rerf.detected_feature_indices_)

        assert rerf.polynomial_features_powers_.shape == (num_terms_in_polynomial, final_num_features), 'PolynomalFeature.power_ shape is incorrect'
        assert rerf.root_model_gradient_coef_.shape == rerf.polynomial_features_powers_.shape, 'Gradient coefficient shape is incorrect'
        assert rerf.fit_X_.shape == (num_train_points, num_terms_in_polynomial), 'Design matrix shape is incorrect'
        assert rerf.partial_hat_matrix_.shape == (num_detected_features, num_detected_features), 'Hat matrix shape is incorrect'

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
        unexplained_variance = residual_sum_of_squares / total_sum_of_squares

        test_threshold = 10 ** -3
        assert (unexplained_variance < test_threshold,
                        f'1 - R^2 = {unexplained_variance} larger than expected ({test_threshold})')

    def test_lasso_categorical_predictions(self):
        rerf = RegressionEnhancedRandomForestRegressionModel(
            model_config=self.model_config,
            input_space=self.test_case_globals['categorical_input_space'],
            output_space=self.test_case_globals['output_space']
        )

        # input space consists of 6 2-d domains that are 5 x 5 units wide.  Hence placing 25 points in each domain.
        num_train_x = 100
        x_train_df, y_train_df = self.generate_points_nonhierarchical_categorical_quadratic(num_train_x)
        rerf.fit(x_train_df, y_train_df)

        num_categorical_levels_expected = len(rerf.one_hot_encoder_adapter.get_one_hot_encoded_column_names())
        num_continuous_dimensions = 2  # x1 and x2
        final_num_features = num_categorical_levels_expected + num_continuous_dimensions
        polynomial_degree = self.model_config.max_basis_function_degree
        num_terms_in_polynomial_per_categorical_level = self.n_choose_k(polynomial_degree + num_continuous_dimensions, num_continuous_dimensions)
        # 1 is added to the num_categorical_levels_expected to account for "level 0" which the one hot encoder in RERF drops the first level,
        # while the design matrix contains a polynomial fit for that level.
        # Since it is possible not all categorical levels will be present in the training set, RERF eliminates zero columns arising from
        # OneHotEncoder knowing the missing levels are possible.  The list of the dropped columns is established in RERF.fit() and used in the
        # RERF.predict() method.
        num_cols_in_design_matrix = num_terms_in_polynomial_per_categorical_level * (num_categorical_levels_expected + 1)\
                                  - len(rerf.categorical_zero_cols_idx_to_delete_)
        num_detected_features = len(rerf.detected_feature_indices_)

        assert rerf.root_model_gradient_coef_.shape == rerf.polynomial_features_powers_.shape, 'Gradient coefficient shape is incorrect'
        assert rerf.fit_X_.shape == (num_train_x, num_cols_in_design_matrix), 'Design matrix shape is incorrect'
        assert rerf.partial_hat_matrix_.shape == (num_detected_features, num_detected_features), 'Hat matrix shape is incorrect'
        assert rerf.polynomial_features_powers_.shape == (num_cols_in_design_matrix, final_num_features), 'PolynomalFeature.power_ shape is incorrect'

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
        test_threshold = 10 ** -3
        assert (unexplained_variance < test_threshold,
                        f'1 - R^2 = {unexplained_variance} larger than expected ({test_threshold})')

    def test_lasso_hierarchical_categorical_predictions(self):
        random.seed(11001)
        objective_function_config = objective_function_config_store.get_config_by_name('three_level_quadratic')
        objective_function = ObjectiveFunctionFactory.create_objective_function(objective_function_config=objective_function_config)

        rerf = RegressionEnhancedRandomForestRegressionModel(
            model_config=self.model_config,
            input_space=objective_function.parameter_space,
            output_space=objective_function.output_space
        )

        # fit model with same degree as true y
        # The input space consists of 3 2-d domains 200 x 200 units.  Hence random samples smaller than a certain size will produce too few points to
        # train reliable models.
        # TODO: Good place to use a non-random training set design
        num_train_x = 600
        x_train_df = objective_function.parameter_space.random_dataframe(num_samples=num_train_x)
        y_train_df = objective_function.evaluate_dataframe(x_train_df)
        rerf.fit(x_train_df, y_train_df)
        num_detected_features = len(rerf.detected_feature_indices_)

        assert rerf.root_model_gradient_coef_.shape == rerf.polynomial_features_powers_.shape, 'Gradient coefficient shape is incorrect'
        assert rerf.fit_X_.shape == (num_train_x, rerf.polynomial_features_powers_.shape[0]), 'Design matrix shape is incorrect'
        assert rerf.partial_hat_matrix_.shape == (num_detected_features, num_detected_features), 'Hat matrix shape is incorrect'
        assert rerf.polynomial_features_powers_.shape == (34, 9), 'PolynomalFeature.power_ shape is incorrect'

        # test predictions
        predicted_value_col = Prediction.LegalColumnNames.PREDICTED_VALUE.value
        num_test_x = 50
        x_test_df = objective_function.parameter_space.random_dataframe(num_samples=num_test_x)
        predictions = rerf.predict(x_test_df)
        pred_df = predictions.get_dataframe()
        predicted_y = pred_df[predicted_value_col].to_numpy()
        y_test = objective_function.evaluate_dataframe(x_test_df).to_numpy().reshape(-1)
        residual_sum_of_squares = ((y_test - predicted_y) ** 2).sum()
        total_sum_of_squares = ((y_test - y_test.mean()) ** 2).sum()
        unexplained_variance = residual_sum_of_squares / total_sum_of_squares
        test_threshold = 10**-3
        assert unexplained_variance < test_threshold, f'1 - R^2 = {unexplained_variance} larger than expected ({test_threshold})'

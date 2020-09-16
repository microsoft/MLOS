#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import unittest
import numpy as np
from scipy import stats

from mlos.OptimizerEvaluationTools.SyntheticFunctions.PolynomialObjective import PolynomialObjective

import mlos.global_values as global_values

global_values.declare_singletons()


class TestPolynomialObjective(unittest.TestCase):

    @classmethod
    def classSetUp(cls):
        global_values.declare_singletons()

    def setUp(self):
        """ Let's create three polynomial response functions that'll be used to test the PolynomialObjective class
            The three polynomial instances are initialized and held in a dictionary together with
            parameters used to create the polynomials
        """
        self.test_polynomials = {
            'generic': {
                'seed': 23,
                'epsilon': 0.01,
                'rand_max_degree': np.random.choice(
                    range(PolynomialObjective.CONFIG_SPACE['max_degree'].min,
                          PolynomialObjective.CONFIG_SPACE['max_degree'].max)),
                'rand_input_domain_dim': np.random.choice(
                    range(PolynomialObjective.CONFIG_SPACE['input_domain_dimension'].min,
                          PolynomialObjective.CONFIG_SPACE['input_domain_dimension'].max)),
                'coefficient_focus': 2.0},
            'generic_without_mixed_terms': {
                'seed': 27,
                'epsilon': 0.01,
                'rand_max_degree': np.random.choice(
                    range(PolynomialObjective.CONFIG_SPACE['max_degree'].min,
                          PolynomialObjective.CONFIG_SPACE['max_degree'].max)),
                'rand_input_domain_dim': np.random.choice(
                    range(PolynomialObjective.CONFIG_SPACE['input_domain_dimension'].min,
                          PolynomialObjective.CONFIG_SPACE['input_domain_dimension'].max)),
                'coefficient_focus': 2.0},
            'generic_with_noise': {
                'seed': 31,
                'epsilon': 0.01,
                'rand_max_degree': 4,  # reduce chances of OOM error in test execution, also runs faster
                'rand_input_domain_dim': 5,  # reduce chances of OOM error in test execution, also runs faster
                'coefficient_focus': 2.0,
                'noise': 0.10}
        }

        # first an arbitrary polynomial from the config space
        shortcut = self.test_polynomials['generic']
        shortcut['poly'] = PolynomialObjective(
            seed=shortcut['seed'],
            max_degree=shortcut['rand_max_degree'],
            coefficient_domain_min=shortcut['coefficient_focus'],
            coefficient_domain_width=shortcut['epsilon'],
            input_domain_dimension=shortcut['rand_input_domain_dim']
        )

        # second arbitrary polynomial without mixed terms
        shortcut = self.test_polynomials['generic_without_mixed_terms']
        shortcut['poly'] = PolynomialObjective(
            seed=shortcut['seed'],
            max_degree=shortcut['rand_max_degree'],
            coefficient_domain_min=shortcut['coefficient_focus'],
            coefficient_domain_width=shortcut['epsilon'],
            input_domain_dimension=shortcut['rand_input_domain_dim'],
            include_mixed_coefficients=False
        )

        # third arbitrary polynomial containing all terms with noise
        shortcut = self.test_polynomials['generic_with_noise']
        shortcut['poly'] = PolynomialObjective(
            seed=shortcut['seed'],
            max_degree=shortcut['rand_max_degree'],
            coefficient_domain_min=shortcut['coefficient_focus'],
            coefficient_domain_width=shortcut['epsilon'],
            input_domain_dimension=shortcut['rand_input_domain_dim'],
            include_noise=True,
            noise_coefficient_of_variation=shortcut['noise']
        )

    def test_general_polynomial_evaluation(self):
        test_setup = self.test_polynomials['generic']
        eval_x = 1.0
        y_min = test_setup['poly'].num_expected_coefficients_ \
            * eval_x ** test_setup['rand_max_degree'] \
            * test_setup['coefficient_focus']
        y_max = test_setup['poly'].num_expected_coefficients_ \
            * eval_x ** test_setup['rand_max_degree'] \
            * (test_setup['coefficient_focus'] + test_setup['epsilon'])

        x = np.array([eval_x] * test_setup['rand_input_domain_dim']).reshape(1, -1)
        y = test_setup['poly'].evaluate(x)[0]

        assert y_min <= y <= y_max

    def test_no_mixed_term_polynomial_evaluation(self):
        test_setup = self.test_polynomials['generic_without_mixed_terms']
        eval_x = 1.0

        y_min = test_setup['rand_input_domain_dim'] \
            * eval_x ** test_setup['rand_max_degree'] \
            * test_setup['coefficient_focus']
        y_max = test_setup['rand_input_domain_dim'] \
            * eval_x ** test_setup['rand_max_degree'] \
            * (test_setup['coefficient_focus'] + test_setup['epsilon'])

        x = np.array([eval_x] * test_setup['rand_input_domain_dim']).reshape(1, -1)
        y = test_setup['poly'].evaluate(x)[0]

        assert y_min <= y <= y_max

    def test_noisy_general_polynomial_evaluation(self):
        test_setup = self.test_polynomials['generic_with_noise']
        eval_x = 1.0
        num_replicates = 1000

        y_min = test_setup['poly'].num_expected_coefficients_ \
            * eval_x ** test_setup['rand_max_degree'] \
            * test_setup['coefficient_focus']
        y_max = test_setup['poly'].num_expected_coefficients_ \
            * eval_x ** test_setup['rand_max_degree'] \
            * (test_setup['coefficient_focus'] + test_setup['epsilon'])

        n = stats.norm.ppf(1 - 0.001)
        y_min_lower_999_confidence_bound = y_min - n * test_setup['noise']
        y_max_upper_999_confidence_bound = y_max + n * test_setup['noise']

        x = np.array([eval_x] * test_setup['rand_input_domain_dim']).reshape(1, -1)
        x = np.tile(x[0], [num_replicates, 1])

        y = test_setup['poly'].evaluate(x)

        assert y_min_lower_999_confidence_bound <= np.mean(y) <= y_max_upper_999_confidence_bound

#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import numpy as np
from sklearn.preprocessing import PolynomialFeatures
from mlos.Logger import create_logger

from mlos.Spaces import CategoricalDimension, ContinuousDimension, DiscreteDimension, Point, SimpleHypergrid


class PolynomialObjective:
    """ A class to enable evaluation of optimizer convergence characteristics.

    An instance allows one to evaluate an arbitrarily high degree (<=16) polynomial objective
    in up to 16 dimensions in which some number of coefficients have been eliminated (set to zero).
    """

    CONFIG_SPACE = SimpleHypergrid(
        name="polynomial_objective_config",
        dimensions=[
            DiscreteDimension(name='seed', min=1, max=2 ** 32),
            DiscreteDimension(name='input_domain_dimension', min=1, max=5),
            DiscreteDimension(name='max_degree', min=1, max=5),
            CategoricalDimension(name='include_mixed_coefficients', values=[False, True]),
            ContinuousDimension(name='percent_coefficients_zeroed', min=0.0, max=1.0),
            ContinuousDimension(name='coefficient_domain_min', min=-2**32, max=2**32),
            ContinuousDimension(name='coefficient_domain_width', min=1, max=2**32),
            CategoricalDimension(name='include_noise', values=[False, True]),
            ContinuousDimension(name='noise_coefficient_of_variation', min=0.0, max=1.0)
        ]
    )
    # needs constraint coefficient_domain_min < coefficient_domain_max

    _DEFAULT = Point(
        seed=17,
        input_domain_dimension=2,
        max_degree=2,
        include_mixed_coefficients=True,
        percent_coefficients_zeroed=0.0,
        coefficient_domain_min=-10.0,
        coefficient_domain_width=9.0,
        include_noise=False,
        noise_coefficient_of_variation=0.0
    )

    """
    Initialization parameters:

    :param coefficients If specified, will override random generation of a polynomial even if `seed` arg is specified
    """

    def __init__(self,
                 seed: int = 17,
                 input_domain_dimension: int = _DEFAULT.input_domain_dimension,
                 max_degree: int = _DEFAULT.max_degree,
                 include_mixed_coefficients: bool = _DEFAULT.include_mixed_coefficients,
                 percent_coefficients_zeroed: float = _DEFAULT.percent_coefficients_zeroed,
                 coefficient_domain_min: float = _DEFAULT.coefficient_domain_min,
                 coefficient_domain_width: float = _DEFAULT.coefficient_domain_width,
                 include_noise: bool = _DEFAULT.include_noise,
                 noise_coefficient_of_variation: float = _DEFAULT.noise_coefficient_of_variation,
                 coefficients=None,
                 logger=None):
        if logger is None:
            logger = create_logger("PolynomialObjective")
        self.logger = logger

        self.seed = seed
        self.input_domain_dimension = input_domain_dimension
        self.max_degree = max_degree
        self.include_mixed_coefficients = include_mixed_coefficients
        self.percent_coefficients_zeroed = percent_coefficients_zeroed
        self.coefficient_domain_min = coefficient_domain_min
        self.coefficient_domain_max = coefficient_domain_min + coefficient_domain_width
        self.coefficients = coefficients
        self.include_noise = include_noise
        self.noise_coefficient_of_variation = noise_coefficient_of_variation

        self.coef_ = []

        # confirm min < max constraint
        assert coefficient_domain_min < self.coefficient_domain_max, 'Minimum coefficient range must be less than maximum'

        self.polynomial_features_ = PolynomialFeatures(degree=self.max_degree)
        discarded_x = np.array([1] * self.input_domain_dimension).reshape(1, -1)
        poly_terms_x = self.polynomial_features_.fit_transform(discarded_x)
        self.num_expected_coefficients_ = len(poly_terms_x[0])

        if coefficients is None:
            # generate random polynomial if coefficients not specified
            np.random.seed(self.seed)

            self.coef_ = [r for r in np.random.uniform(self.coefficient_domain_min,
                                                       self.coefficient_domain_max,
                                                       self.num_expected_coefficients_)
                          ]  # temporarily a list to be convert to np.array

            if self.percent_coefficients_zeroed > 0.0:
                # reset a random subset of coefficients to 0
                num_coef_to_zero = int(self.percent_coefficients_zeroed * self.num_expected_coefficients_)
                true_poly_term_indices_without_effects = np.random.choice(range(self.num_expected_coefficients_),
                                                                          size=num_coef_to_zero,
                                                                          replace=False)
                for zi in true_poly_term_indices_without_effects:
                    self.coef_[zi] = 0.0

            # eliminate mixed variable terms if requested
            if not self.include_mixed_coefficients:
                # zero term coef where input's power != max_degree
                for ip, p in enumerate(self.polynomial_features_.powers_):
                    max_variable_degree = np.max(p)
                    if max_variable_degree != self.max_degree:
                        self.coef_[ip] = 0.0

            # convert to np.array to enable matmul evaluations
            self.coef_ = np.array(self.coef_)

        else:
            # test if degree specified is consistent with number of coefficients passed
            num_specified_coefficients = len(self.coefficients)
            assert num_specified_coefficients == self.num_expected_coefficients_, \
                'Failed to find sufficient number of coefficients for specified polynomial degree'

            self.coef_ = np.array(self.coefficients)

    def evaluate(self, x):
        y = np.matmul(self.polynomial_features_.fit_transform(x),
                      self.coef_)
        if self.include_noise:
            cv = self.noise_coefficient_of_variation

            y_cv = np.tile(cv, [len(y)])
            y_std = np.abs(y_cv * y)
            y = np.random.normal(y, y_std, [len(y)])

        return y

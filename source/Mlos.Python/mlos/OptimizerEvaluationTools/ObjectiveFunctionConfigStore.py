#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from mlos.Spaces import Point, SimpleHypergrid, CategoricalDimension
from mlos.Spaces.Configs import ComponentConfigStore
from mlos.OptimizerEvaluationTools.SyntheticFunctions.PolynomialObjective import PolynomialObjective
from mlos.OptimizerEvaluationTools.SyntheticFunctions.ThreeLevelQuadratic import ThreeLevelQuadratic
from mlos.OptimizerEvaluationTools.SyntheticFunctions.Flower import Flower

objective_function_config_store = ComponentConfigStore(
    parameter_space=SimpleHypergrid(
        name="objective_function",
        dimensions=[
            CategoricalDimension(name="implementation", values=[
                PolynomialObjective.__name__,
                ThreeLevelQuadratic.__name__,
                Flower.__name__,
            ])
        ]
    ).join(
        subgrid=PolynomialObjective.CONFIG_SPACE,
        on_external_dimension=CategoricalDimension(name="implementation", values=[PolynomialObjective.__name__])
    ),
    default=Point(
        implementation=PolynomialObjective.__name__,
        # TODO: move polynomial objective to config store
        polynomial_objective_config=PolynomialObjective._DEFAULT, # pylint: disable=protected-access,
    )
)

objective_function_config_store.add_config_by_name(
    config_name="three_level_quadratic",
    config_point=Point(implementation=ThreeLevelQuadratic.__name__)
)

objective_function_config_store.add_config_by_name(
    config_name="flower",
    config_point=Point(implementation=Flower.__name__)
)

objective_function_config_store.add_config_by_name(
    config_name="noisy_polynomial_objective",
    config_point=Point(
        implementation=PolynomialObjective.__name__,
        polynomial_objective_config=Point(
            seed=17,
            input_domain_dimension=2,
            max_degree=2,
            include_mixed_coefficients=True,
            percent_coefficients_zeroed=0.0,
            coefficient_domain_min=-10.0,
            coefficient_domain_width=9.0,
            include_noise=True,
            noise_coefficient_of_variation=0.2
        )
    )
)

objective_function_config_store.add_config_by_name(
    config_name="2d_quadratic_concave_down",
    config_point=Point(
        implementation=PolynomialObjective.__name__,
        polynomial_objective_config=Point(
            seed=19,
            input_domain_dimension=2,
            max_degree=2,
            include_mixed_coefficients=True,
            percent_coefficients_zeroed=0.0,
            coefficient_domain_min=-10.0,
            coefficient_domain_width=9.0,
            include_noise=True,
            noise_coefficient_of_variation=0.2
        )
    )
)

objective_function_config_store.add_config_by_name(
    config_name="2d_quadratic_concave_up",
    config_point=Point(
        implementation=PolynomialObjective.__name__,
        polynomial_objective_config=Point(
            seed=19,
            input_domain_dimension=2,
            max_degree=2,
            include_mixed_coefficients=True,
            percent_coefficients_zeroed=0.0,
            coefficient_domain_min=1.0,
            coefficient_domain_width=9.0,
            include_noise=True,
            noise_coefficient_of_variation=0.2
        )
    )
)

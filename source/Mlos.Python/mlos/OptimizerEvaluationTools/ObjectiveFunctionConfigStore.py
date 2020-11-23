#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from mlos.Spaces import CategoricalDimension, ContinuousDimension, DiscreteDimension, Point, SimpleHypergrid
from mlos.Spaces.Configs import ComponentConfigStore
from mlos.OptimizerEvaluationTools.SyntheticFunctions.Flower import Flower
from mlos.OptimizerEvaluationTools.SyntheticFunctions.Hypersphere import Hypersphere
from mlos.OptimizerEvaluationTools.SyntheticFunctions.NestedPolynomialObjective import NestedPolynomialObjective
from mlos.OptimizerEvaluationTools.SyntheticFunctions.PolynomialObjective import PolynomialObjective
from mlos.OptimizerEvaluationTools.SyntheticFunctions.ThreeLevelQuadratic import ThreeLevelQuadratic

objective_function_config_store = ComponentConfigStore(
    parameter_space=SimpleHypergrid(
        name="objective_function",
        dimensions=[
            CategoricalDimension(name="implementation", values=[
                Flower.__name__,
                NestedPolynomialObjective.__name__,
                PolynomialObjective.__name__,
                ThreeLevelQuadratic.__name__,
                Hypersphere.__name__
            ])
        ]
    ).join(
        subgrid=PolynomialObjective.CONFIG_SPACE,
        on_external_dimension=CategoricalDimension(name="implementation", values=[PolynomialObjective.__name__])
    ).join(
        subgrid=SimpleHypergrid(
            name="nested_polynomial_objective_config",
            dimensions=[
                DiscreteDimension(name="num_nested_polynomials", min=1, max=128),
                CategoricalDimension(name="nested_function_implementation", values=[PolynomialObjective.__name__])
            ]
        ).join(
            subgrid=PolynomialObjective.CONFIG_SPACE,
            on_external_dimension=CategoricalDimension(name="nested_function_implementation", values=[PolynomialObjective.__name__])
        ),
        on_external_dimension=CategoricalDimension(name="implementation", values=[NestedPolynomialObjective.__name__])
    ).join(
        subgrid=SimpleHypergrid(
            name="hypersphere_config",
            dimensions=[
                DiscreteDimension(name="num_objectives", min=1, max=100),
                CategoricalDimension(name="minimize", values=["all", "none", "some"]),
                ContinuousDimension(name="radius", min=0, max=100, include_min=False)
            ]
        ),
        on_external_dimension=CategoricalDimension(name="implementation", values=[Hypersphere.__name__])
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
            input_domain_min=-2**10,
            input_domain_width=2**11,
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
            input_domain_min=-2**10,
            input_domain_width=2**11,
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
            input_domain_min=-2**10,
            input_domain_width=2**11,
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

objective_function_config_store.add_config_by_name(
    config_name="2d_quadratic_concave_up_no_noise",
    config_point=Point(
        implementation=PolynomialObjective.__name__,
        polynomial_objective_config=Point(
            seed=19,
            input_domain_dimension=2,
            input_domain_min=-2**10,
            input_domain_width=2**11,
            max_degree=2,
            include_mixed_coefficients=True,
            percent_coefficients_zeroed=0.0,
            coefficient_domain_min=1.0,
            coefficient_domain_width=9.0,
            include_noise=False,
            noise_coefficient_of_variation=0.0
        )
    )
)

objective_function_config_store.add_config_by_name(
    config_name="5_mutually_exclusive_polynomials",
    config_point=Point(
        implementation=NestedPolynomialObjective.__name__,
        nested_polynomial_objective_config=Point(
            num_nested_polynomials=5,
            nested_function_implementation=PolynomialObjective.__name__,
            polynomial_objective_config=Point(
                seed=17,
                input_domain_dimension=2,
                input_domain_min=-2**10,
                input_domain_width=2**11,
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
)

for num_objectives in [2, 10]:
    for minimize in ["all", "none", "some"]:
        objective_function_config_store.add_config_by_name(
            config_name=f"{num_objectives}d_hypersphere_minimize_{minimize}",
            config_point=Point(
                implementation=Hypersphere.__name__,
                hypersphere_config=Point(
                    num_objectives=num_objectives,
                    minimize=minimize,
                    radius=10
                )
            ),
            description=f"An objective function with {num_objectives + 1} parameters "
                        f"and {num_objectives} objectives to maximize."
        )

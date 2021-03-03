#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from mlos.OptimizerEvaluationTools.SyntheticFunctions.EnvelopedWaves import EnvelopedWaves, enveloped_waves_config_store
from mlos.OptimizerEvaluationTools.SyntheticFunctions.Flower import Flower
from mlos.OptimizerEvaluationTools.SyntheticFunctions.Hypersphere import Hypersphere
from mlos.OptimizerEvaluationTools.SyntheticFunctions.HypersphereConfigStore import hypersphere_config_store
from mlos.OptimizerEvaluationTools.SyntheticFunctions.MultiObjectiveNestedPolynomialObjective import MultiObjectiveNestedPolynomialObjective, \
    multi_objective_nested_polynomial_config_space
from mlos.OptimizerEvaluationTools.SyntheticFunctions.MultiObjectiveEnvelopedWaves import MultiObjectiveEnvelopedWaves, \
    multi_objective_enveloped_waves_config_store
from mlos.OptimizerEvaluationTools.SyntheticFunctions.NestedPolynomialObjective import NestedPolynomialObjective, nested_polynomial_objective_config_space
from mlos.OptimizerEvaluationTools.SyntheticFunctions.PolynomialObjective import PolynomialObjective
from mlos.OptimizerEvaluationTools.SyntheticFunctions.ThreeLevelQuadratic import ThreeLevelQuadratic
from mlos.Spaces import CategoricalDimension, Point, SimpleHypergrid
from mlos.Spaces.Configs import ComponentConfigStore

objective_function_config_store = ComponentConfigStore(
    parameter_space=SimpleHypergrid(
        name="objective_function_config",
        dimensions=[
            CategoricalDimension(name="implementation", values=[
                EnvelopedWaves.__name__,
                Flower.__name__,
                NestedPolynomialObjective.__name__,
                PolynomialObjective.__name__,
                ThreeLevelQuadratic.__name__,
                Hypersphere.__name__,
                MultiObjectiveNestedPolynomialObjective.__name__,
                MultiObjectiveEnvelopedWaves.__name__,
            ])
        ]
    ).join(
        subgrid=PolynomialObjective.CONFIG_SPACE,
        on_external_dimension=CategoricalDimension(name="implementation", values=[PolynomialObjective.__name__])
    ).join(
        subgrid=nested_polynomial_objective_config_space,
        on_external_dimension=CategoricalDimension(name="implementation", values=[NestedPolynomialObjective.__name__])
    ).join(
        subgrid=hypersphere_config_store.parameter_space,
        on_external_dimension=CategoricalDimension(name="implementation", values=[Hypersphere.__name__])
    ).join(
        subgrid=multi_objective_nested_polynomial_config_space,
        on_external_dimension=CategoricalDimension(name="implementation", values=[MultiObjectiveNestedPolynomialObjective.__name__])
    ).join(
        subgrid=enveloped_waves_config_store.parameter_space,
        on_external_dimension=CategoricalDimension(name="implementation", values=[EnvelopedWaves.__name__])
    ).join(
        subgrid=multi_objective_enveloped_waves_config_store.parameter_space,
        on_external_dimension=CategoricalDimension(name="implementation", values=[MultiObjectiveEnvelopedWaves.__name__])
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

for named_hypersphere_config in hypersphere_config_store.list_named_configs():
    objective_function_config_store.add_config_by_name(
        config_name=named_hypersphere_config.name,
        config_point=Point(
            implementation=Hypersphere.__name__,
            hypersphere_config=named_hypersphere_config.config_point,
            description=named_hypersphere_config.description
        )
    )

objective_function_config_store.add_config_by_name(
    config_name="multi_objective_2_mutually_exclusive_polynomials",
    config_point=Point(
        implementation=MultiObjectiveNestedPolynomialObjective.__name__,
        multi_objective_nested_polynomial_config=Point(
            num_objectives=2,
            objective_function_implementation=NestedPolynomialObjective.__name__,
            nested_polynomial_objective_config=Point(
                num_nested_polynomials=2,
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
                    include_noise=False,
                    noise_coefficient_of_variation=0.0
                )
            )
        )
    )
)

objective_function_config_store.add_config_by_name(
    config_name="multi_objective_waves_3_params_2_objectives_no_phase_difference",
    config_point=Point(
        implementation=MultiObjectiveEnvelopedWaves.__name__,
        multi_objective_enveloped_waves_config=multi_objective_enveloped_waves_config_store.get_config_by_name("no_phase_difference")
    )
)

objective_function_config_store.add_config_by_name(
    config_name="multi_objective_waves_3_params_2_objectives_half_pi_phase_difference",
    config_point=Point(
        implementation=MultiObjectiveEnvelopedWaves.__name__,
        multi_objective_enveloped_waves_config=multi_objective_enveloped_waves_config_store.get_config_by_name("half_pi_phase_difference")
    )
)

objective_function_config_store.add_config_by_name(
    config_name="multi_objective_waves_3_params_2_objectives_pi_phase_difference",
    config_point=Point(
        implementation=MultiObjectiveEnvelopedWaves.__name__,
        multi_objective_enveloped_waves_config=multi_objective_enveloped_waves_config_store.get_config_by_name("pi_phase_difference")
    )
)

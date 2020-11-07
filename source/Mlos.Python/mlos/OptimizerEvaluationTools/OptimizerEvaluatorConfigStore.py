#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from mlos.Spaces import CategoricalDimension, DiscreteDimension, Point, SimpleHypergrid
from mlos.Spaces.Configs import ComponentConfigStore

optimizer_evaluator_config_store = ComponentConfigStore(
    description="Describes the configuration space for the OptimizerEvaluator.\n"
                "\n"
                "Dimensions:\n"
                "- num_iterations: how many optimization iterations to run.\n"
                "- evaluation_frequency: how often should the evaluator capture the optima and goodness of fit metrics (e.g. every 10 iterations).\n"
                "- include_pickled_optimizer_in_report: should the state of the optimizer be pickled and saved.\n"
                "- include_pickled_objective_function_in_report: should the final state of the objective function be pickled and saved.\n"
                "- report_regression_model_goodness_of_fit: should the goodness of fit metrics be included in the evaluation report.\n"
                "- report_optima_over_time: should the optima over time be included in the evaluation report.\n"
                "- include_execution_trace_in_report: should the execution trace produced by mlos.Tracer be included in the evaluation report.",

    parameter_space=SimpleHypergrid(
        name="optimizer_evaluator",
        dimensions=[
            DiscreteDimension(name="num_iterations", min=1, max=2**32),
            DiscreteDimension(name="evaluation_frequency", min=1, max=2**10),
            CategoricalDimension(name="include_pickled_optimizer_in_report", values=[True, False]),
            CategoricalDimension(name="include_pickled_objective_function_in_report", values=[True, False]),
            CategoricalDimension(name="report_regression_model_goodness_of_fit", values=[True, False]),
            CategoricalDimension(name="report_optima_over_time", values=[True, False]),
            CategoricalDimension(name="include_execution_trace_in_report", values=[True, False]),
        ]
    ),
    default=Point(
        num_iterations=100,
        evaluation_frequency=10,
        include_pickled_optimizer_in_report=True,
        include_pickled_objective_function_in_report=True,
        report_regression_model_goodness_of_fit=True,
        report_optima_over_time=True,
        include_execution_trace_in_report=True,
    )
)


# Parallel unit tests config.
#
parallel_unit_tests_config = optimizer_evaluator_config_store.default
parallel_unit_tests_config.num_iterations = 50
parallel_unit_tests_config.evaluation_frequency = 10
optimizer_evaluator_config_store.add_config_by_name(
    config_name="parallel_unit_tests_config",
    description="This config is to be used in our parallel unit tests.",
    config_point=parallel_unit_tests_config
)

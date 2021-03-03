#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import copy
from datetime import datetime
import pickle
import traceback

import mlos.global_values
from mlos.Logger import create_logger
from mlos.OptimizerEvaluationTools.ObjectiveFunctionBase import ObjectiveFunctionBase
from mlos.OptimizerEvaluationTools.ObjectiveFunctionFactory import ObjectiveFunctionFactory, objective_function_config_store
from mlos.OptimizerEvaluationTools.OptimizerEvaluationReport import OptimizerEvaluationReport
from mlos.OptimizerEvaluationTools.OptimizerEvaluatorConfigStore import optimizer_evaluator_config_store
from mlos.OptimizerEvaluationTools.OptimumOverTime import OptimumOverTime
from mlos.Optimizers.BayesianOptimizerFactory import BayesianOptimizerFactory, bayesian_optimizer_config_store
from mlos.Optimizers.OptimizerBase import OptimizerBase
from mlos.Optimizers.OptimumDefinition import OptimumDefinition
from mlos.Optimizers.RegressionModels.GoodnessOfFitMetrics import DataSetType
from mlos.Optimizers.RegressionModels.MultiObjectiveRegressionModelFitState import MultiObjectiveRegressionModelFitState
from mlos.Optimizers.RegressionModels.RegressionModelFitState import RegressionModelFitState
from mlos.Spaces import Point
from mlos.Tracer import trace, traced, Tracer


class OptimizerEvaluator:
    """Evaluates optimizers against objective functions.

    This class is responsible for:

        1. instantiating an optimizer
        2. instantiating an objective function
        3. launching an optimizer against that objective function
        4. keeping track of the goodness of fit, and of the various optima over time
        5. producing an instance of OptimizerEvaluationReport.

    """

    def __init__(
            self,
            optimizer_evaluator_config: Point,
            optimizer: OptimizerBase = None,
            optimizer_config: Point = None,
            objective_function: ObjectiveFunctionBase = None,
            objective_function_config: Point = None,
            logger = None
    ):
        assert optimizer_evaluator_config in optimizer_evaluator_config_store.parameter_space
        assert (optimizer is None) != (optimizer_config is None), "A valid optimizer XOR a valid optimizer_config must be supplied."
        assert (objective_function is None) != (objective_function_config is None),\
            "A valid objective_function XOR a valid objective_function_config must be specified"

        if logger is None:
            logger = create_logger("OptimizerEvaluator")
        self.logger = logger

        self.optimizer_evaluator_config = optimizer_evaluator_config
        self.objective_function_config = None
        self.objective_function = None
        self.optimizer_config = None
        self.optimizer = None

        # Let's get the objective function assigned to self's fields.
        #
        if (objective_function_config is not None) and (objective_function is None):
            assert objective_function_config in objective_function_config_store.parameter_space
            self.objective_function_config = objective_function_config
            self.objective_function = ObjectiveFunctionFactory.create_objective_function(objective_function_config)

        elif (objective_function is not None) and (objective_function_config is None):
            self.objective_function_config = objective_function.objective_function_config
            self.objective_function = objective_function

        else:
            # The assert above should have caught it but just in case someone removes or changes it.
            #
            assert False, "A valid objective_function XOR a valid objective_function_config must be specified"

        # Let's get the optimizer and its config assigned to self's fields.
        #
        if (optimizer_config is not None) and (optimizer is None):
            assert optimizer_config in bayesian_optimizer_config_store.parameter_space
            optimization_problem = self.objective_function.default_optimization_problem
            self.optimizer_config = optimizer_config
            self.optimizer = BayesianOptimizerFactory().create_local_optimizer(
                optimizer_config=optimizer_config,
                optimization_problem=optimization_problem
            )

        elif (optimizer is not None) and (optimizer_config is None):
            # TODO: assert that the optimization problem in the optimizer matches the objective function.
            # But this requires Hypergrid.__eq__.
            #
            self.optimizer_config = optimizer.optimizer_config
            self.optimizer = optimizer

        else:
            # Again, the assert at the beginning of the constructor should have caught this. But more asserts => less bugs.
            #
            assert False, "A valid optimizer XOR a valid optimizer_config must be supplied."


    @trace()
    def evaluate_optimizer(self) -> OptimizerEvaluationReport: # pylint: disable=too-many-statements,too-many-branches
        evaluation_report = OptimizerEvaluationReport(
            optimizer_configuration=self.optimizer_config,
            objective_function_configuration=self.objective_function_config,
            num_optimization_iterations=self.optimizer_evaluator_config.num_iterations,
            evaluation_frequency=self.optimizer_evaluator_config.evaluation_frequency
        )

        if self.optimizer_evaluator_config.include_execution_trace_in_report:
            mlos.global_values.declare_singletons()
            if mlos.global_values.tracer is None:
                mlos.global_values.tracer = Tracer()
            mlos.global_values.tracer.clear_events()


        if self.optimizer_evaluator_config.include_pickled_objective_function_in_report:
            evaluation_report.pickled_objective_function_initial_state = pickle.dumps(self.objective_function)

        if self.optimizer_evaluator_config.include_pickled_optimizer_in_report:
            evaluation_report.pickled_optimizer_initial_state = pickle.dumps(self.optimizer)

        multi_objective_regression_model_fit_state = MultiObjectiveRegressionModelFitState(objective_names=self.optimizer.optimization_problem.objective_names)
        for objective_name in self.optimizer.optimization_problem.objective_names:
            multi_objective_regression_model_fit_state[objective_name] = RegressionModelFitState()

        optima_over_time = {}
        optima_over_time[OptimumDefinition.BEST_OBSERVATION.value] = OptimumOverTime(
            optimization_problem=self.optimizer.optimization_problem,
            optimum_definition=OptimumDefinition.BEST_OBSERVATION
        )

        optima_over_time[OptimumDefinition.PREDICTED_VALUE_FOR_OBSERVED_CONFIG.value] = OptimumOverTime(
            optimization_problem=self.optimizer.optimization_problem,
            optimum_definition=OptimumDefinition.PREDICTED_VALUE_FOR_OBSERVED_CONFIG
        )

        optima_over_time[f"{OptimumDefinition.UPPER_CONFIDENCE_BOUND_FOR_OBSERVED_CONFIG.value}_99"] = OptimumOverTime(
            optimization_problem=self.optimizer.optimization_problem,
            optimum_definition=OptimumDefinition.UPPER_CONFIDENCE_BOUND_FOR_OBSERVED_CONFIG,
            alpha=0.01
        )

        optima_over_time[f"{OptimumDefinition.LOWER_CONFIDENCE_BOUND_FOR_OBSERVED_CONFIG.value}_99"] = OptimumOverTime(
            optimization_problem=self.optimizer.optimization_problem,
            optimum_definition=OptimumDefinition.LOWER_CONFIDENCE_BOUND_FOR_OBSERVED_CONFIG,
            alpha=0.01
        )

        #####################################################################################################
        evaluation_report.start_time = datetime.utcnow()
        i = 0
        try:
            with traced(scope_name="optimization_loop"):
                for i in range(self.optimizer_evaluator_config.num_iterations):
                    parameters = self.optimizer.suggest()
                    objectives = self.objective_function.evaluate_point(parameters)
                    self.optimizer.register(parameters.to_dataframe(), objectives.to_dataframe())

                    if i % self.optimizer_evaluator_config.evaluation_frequency == 0:
                        self.logger.info(f"[{i + 1}/{self.optimizer_evaluator_config.num_iterations}]")
                        with traced(scope_name="evaluating_optimizer"):
                            if self.optimizer_evaluator_config.include_pickled_optimizer_in_report:
                                evaluation_report.add_pickled_optimizer(iteration=i, pickled_optimizer=pickle.dumps(self.optimizer))

                            if self.optimizer.trained:
                                multi_objective_gof_metrics = self.optimizer.compute_surrogate_model_goodness_of_fit()
                                for objective_name, gof_metrics in multi_objective_gof_metrics:
                                    multi_objective_regression_model_fit_state[objective_name].set_gof_metrics(
                                        data_set_type=DataSetType.TRAIN,
                                        gof_metrics=gof_metrics
                                    )

                            for optimum_name, optimum_over_time in optima_over_time.items():
                                try:
                                    config, value = self.optimizer.optimum(
                                        optimum_definition=optimum_over_time.optimum_definition,
                                        alpha=optimum_over_time.alpha
                                    )
                                    optima_over_time[optimum_name].add_optimum_at_iteration(
                                        iteration=i,
                                        optimum_config=config,
                                        optimum_value=value
                                    )
                                except ValueError as e:
                                    self.logger.info(f"Failed to get {optimum_name} optimum.", exc_info=True)

                            if self.optimizer_evaluator_config.report_pareto_over_time:
                                evaluation_report.pareto_over_time[i] = copy.deepcopy(self.optimizer.optimization_problem)

                            if self.optimizer_evaluator_config.report_pareto_volume_over_time:
                                volume_estimator = self.optimizer.pareto_frontier.approximate_pareto_volume()
                                ci99_on_volume = volume_estimator.get_two_sided_confidence_interval_on_pareto_volume(alpha=0.01)
                                evaluation_report.pareto_volume_over_time[i] = ci99_on_volume

                evaluation_report.success = True

        except Exception as e:
            evaluation_report.success = False
            evaluation_report.exception = e
            evaluation_report.exception_traceback = traceback.format_exc()

        evaluation_report.end_time = datetime.utcnow()

        with traced(scope_name="evaluating_optimizer"):
            # Once the optimization is done, we perform a final evaluation of the optimizer.

            if self.optimizer.trained:
                multi_objective_gof_metrics = self.optimizer.compute_surrogate_model_goodness_of_fit()
                for objective_name, gof_metrics in multi_objective_gof_metrics:
                    multi_objective_regression_model_fit_state[objective_name].set_gof_metrics(data_set_type=DataSetType.TRAIN, gof_metrics=gof_metrics)

            for optimum_name, optimum_over_time in optima_over_time.items():
                try:
                    config, value = self.optimizer.optimum(optimum_definition=optimum_over_time.optimum_definition, alpha=optimum_over_time.alpha)
                    optima_over_time[optimum_name].add_optimum_at_iteration(
                        iteration=self.optimizer_evaluator_config.num_iterations,
                        optimum_config=config,
                        optimum_value=value
                    )
                except Exception as e:
                    self.logger.info(f"Failed to get {optimum_name} optimum.", exc_info=True)

        if self.optimizer_evaluator_config.report_pareto_over_time:
            evaluation_report.pareto_over_time[i] = copy.deepcopy(self.optimizer.optimization_problem)

        if self.optimizer_evaluator_config.report_pareto_volume_over_time:
            volume_estimator = self.optimizer.pareto_frontier.approximate_pareto_volume()
            ci99_on_volume = volume_estimator.get_two_sided_confidence_interval_on_pareto_volume(alpha=0.01)
            evaluation_report.pareto_volume_over_time[i] = ci99_on_volume

        if self.optimizer_evaluator_config.include_execution_trace_in_report:
            evaluation_report.execution_trace = mlos.global_values.tracer.trace_events
            mlos.global_values.tracer.clear_events()

        if self.optimizer_evaluator_config.include_pickled_optimizer_in_report:
            evaluation_report.add_pickled_optimizer(iteration=i, pickled_optimizer=pickle.dumps(self.optimizer))

        if self.optimizer_evaluator_config.include_pickled_objective_function_in_report:
            evaluation_report.pickled_objective_function_final_state = pickle.dumps(self.objective_function)

        if self.optimizer_evaluator_config.report_regression_model_goodness_of_fit:
            evaluation_report.regression_model_fit_state = multi_objective_regression_model_fit_state

        if self.optimizer_evaluator_config.report_optima_over_time:
            evaluation_report.optima_over_time = optima_over_time

        return evaluation_report

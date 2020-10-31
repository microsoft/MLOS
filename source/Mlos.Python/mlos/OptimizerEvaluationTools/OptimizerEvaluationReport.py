#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import json
import os
import pickle
from typing import Dict, List
from mlos.Logger import BufferingHandler, create_logger
from mlos.OptimizerEvaluationTools.OptimumOverTime import OptimumOverTime
from mlos.Optimizers.RegressionModels.RegressionModelFitState import RegressionModelFitState
from mlos.Spaces import Point
from mlos.Tracer import trace, Tracer


class OptimizerEvaluationReport:
    """Contains all information gathered during an optimizer evaluation run.

    This includes:
        * optimizer configuration
        * objective function configuration
        * serialized optimizer (with random seeds, and all observations)
        * serialized objective function (with random seeds)
        * evaluation parameters:
            * num optimization iterations
            * evaluation frequency
        * optimizer's regression model goodness of fit metrics over time
        * optima over time for the following definitions:
            * best observation
            * best predicted value for observed config
            * best upper confidence bound on a 99% confidence interval for an observed config
            * best lower confidence bound on a 99% confidence interval for an observed config
        * execution trace as captured by the mlos.Tracer
    """

    def __init__(
        self,
        optimizer_configuration: Point = None,
        objective_function_configuration: Point = None,
        pickled_objective_function_initial_state: str = None,
        pickled_objective_function_final_state: str = None,
        num_optimization_iterations: int = None,
        evaluation_frequency: int = None,
        regression_model_goodness_of_fit_state: RegressionModelFitState = None,
        optima_over_time: Dict[str, OptimumOverTime] = None,
        execution_trace: List[Dict[str, object]] = None
    ):
        self.success = False
        self.exception = None
        self.exception_traceback = None

        self.optimizer_configuration = optimizer_configuration
        self.objective_function_configuration = objective_function_configuration

        # Dictionary with iteration number as key and pickled optimizer as value
        #
        self.pickled_optimizers_over_time: Dict[int, bytes] = {}
        self.pickled_objective_function_initial_state = pickled_objective_function_initial_state
        self.pickled_objective_function_final_state = pickled_objective_function_final_state
        self.num_optimization_iterations = num_optimization_iterations
        self.evaluation_frequency = evaluation_frequency
        self.regression_model_goodness_of_fit_state = regression_model_goodness_of_fit_state
        self.optima_over_time = optima_over_time
        self.execution_trace = execution_trace

    @trace()
    def add_pickled_optimizer(self, iteration: int, pickled_optimizer: bytes):
        assert iteration >= 0
        self.pickled_optimizers_over_time[iteration] = pickled_optimizer

    def write_to_disk(self, target_folder):
        """Writes the report to disk.

        The layout on disk is as follows:
        - optimizer_config.json
        - objective_function_config.json
        - goodness_of_fit.pickle
        - objective_function_initial_state.pickle
        - objective_function_final_state.pickle
        - execution_trace.json
        - execution_info.json
        - pickled_optimizers:
            - {iteration_number}.pickle

        """
        optimizer_config_file = os.path.join(target_folder, "optimizer_config.json")
        with open(optimizer_config_file, 'w') as out_file:
            out_file.write(self.optimizer_configuration.to_json(indent=2))

        objective_function_config_file = os.path.join(target_folder, "objective_function_config.json")
        with open(objective_function_config_file, 'w') as out_file:
            out_file.write(self.objective_function_configuration.to_json(indent=2))

        if len(self.pickled_optimizers_over_time) > 0:
            pickled_optimizers_dir = os.path.join(target_folder, "pickled_optimizers")
            if not os.path.exists(pickled_optimizers_dir):
                os.mkdir(pickled_optimizers_dir)
            for iteration, pickled_optimizer in self.pickled_optimizers_over_time.items():
                with open(os.path.join(pickled_optimizers_dir, f"{iteration}.pickle"), 'wb') as out_file:
                    out_file.write(pickled_optimizer)

        if self.pickled_objective_function_initial_state is not None:
            with open(os.path.join(target_folder, "objective_function_initial_state.pickle"), "wb") as out_file:
                out_file.write(self.pickled_objective_function_initial_state)

        if self.pickled_objective_function_final_state is not None:
            with open(os.path.join(target_folder, "objective_function_final_state.pickle"), "wb") as out_file:
                out_file.write(self.pickled_objective_function_final_state)

        if self.regression_model_goodness_of_fit_state is not None:
            with open(os.path.join(target_folder, "goodness_of_fit.pickle"), "wb") as out_file:
                pickle.dump(self.regression_model_goodness_of_fit_state, out_file)

        if self.optima_over_time is not None:
            with open(os.path.join(target_folder, "optima_over_time.pickle"), "wb") as out_file:
                pickle.dump(self.optima_over_time, out_file)

        if self.execution_trace is not None:
            tracer = Tracer()
            tracer.trace_events = self.execution_trace
            tracer.dump_trace_to_file(output_file_path=os.path.join(target_folder, "execution_trace.json"))

        with open(os.path.join(target_folder, "execution_info.json"), 'w') as out_file:
            execution_info_dict = {
                'success': self.success,
                'num_optimization_iterations': self.num_optimization_iterations,
                'evaluation_frequency': self.evaluation_frequency,
                'exception': str(self.exception),
                'exception_stack_trace': self.exception_traceback
            }
            json.dump(execution_info_dict, out_file, indent=2)




#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from datetime import datetime
import json
import os
import pickle
from typing import Dict, List, Tuple
from mlos.OptimizerEvaluationTools.OptimumOverTime import OptimumOverTime
from mlos.Optimizers.ParetoFrontier import ParetoFrontier
from mlos.Optimizers.RegressionModels.MultiObjectiveRegressionModelFitState import MultiObjectiveRegressionModelFitState
from mlos.Spaces import Point
from mlos.Tracer import Tracer


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
            regression_model_goodness_of_fit_state: MultiObjectiveRegressionModelFitState = None,
            optima_over_time: Dict[str, OptimumOverTime] = None,
            pareto_over_time: Dict[int, ParetoFrontier] = None,
            pareto_volume_over_time: Dict[int, Tuple[float, float]] = None,
            execution_trace: List[Dict[str, object]] = None,
            start_time: datetime = None,
            end_time: datetime = None,
            suggestion: Point = None
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
        self.regression_model_fit_state = regression_model_goodness_of_fit_state
        self.optima_over_time = optima_over_time
        self.execution_trace = execution_trace
        self.pareto_over_time = pareto_over_time if pareto_over_time is not None else dict()
        self.pareto_volume_over_time = pareto_volume_over_time if pareto_volume_over_time is not None else dict()
        self.start_time = start_time
        self.end_time = end_time
        self.suggestion = suggestion

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

        if self.regression_model_fit_state is not None:
            with open(os.path.join(target_folder, "regression_model_goodness_of_fit_state.pickle"), "wb") as out_file:
                pickle.dump(self.regression_model_fit_state, out_file)

        if self.optima_over_time is not None:
            with open(os.path.join(target_folder, "optima_over_time.pickle"), "wb") as out_file:
                pickle.dump(self.optima_over_time, out_file)

        if len(self.pareto_over_time) > 0:
            with open(os.path.join(target_folder, "pareto_over_time.pickle"), "wb") as out_file:
                pickle.dump(self.pareto_over_time, out_file)

        if len(self.pareto_volume_over_time) > 0:
            with open(os.path.join(target_folder, "pareto_volume_over_time.json"), "w") as out_file:
                json.dump(self.pareto_volume_over_time, out_file, indent=2)

        if self.execution_trace is not None:
            tracer = Tracer()
            tracer.trace_events = self.execution_trace
            tracer.dump_trace_to_file(output_file_path=os.path.join(target_folder, "execution_trace.json"))

        with open(os.path.join(target_folder, "execution_info.json"), 'w') as out_file:
            execution_info_dict = {
                'success': self.success,
                'num_optimization_iterations': self.num_optimization_iterations,
                'evaluation_frequency': self.evaluation_frequency,
                'exception': str(self.exception) if self.exception is not None else None,
                'exception_stack_trace': self.exception_traceback,
                'start_time': self.start_time.strftime("%d.%m.%Y.%H:%M:%S:%f"),
                'end_time': self.end_time.strftime("%d.%m.%Y.%H:%M:%S:%f")
            }
            json.dump(execution_info_dict, out_file, indent=2)

    @staticmethod
    def read_from_disk(target_folder):
        """Mirrors write_to_disk by reading into memory the contents of an OptimizerEvaluationReport from disk."""

        optimizer_evaluation_report = OptimizerEvaluationReport()

        optimizer_config_file = os.path.join(target_folder, "optimizer_config.json")
        with open(optimizer_config_file, 'r') as in_file:
            optimizer_evaluation_report.optimizer_configuration = Point.from_json(in_file.read())

        objective_function_config_file = os.path.join(target_folder, "objective_function_config.json")
        with open(objective_function_config_file, 'r') as in_file:
            optimizer_evaluation_report.objective_function_configuration = Point.from_json(in_file.read())

        pickled_optimizers_dir = os.path.join(target_folder, "pickled_optimizers")
        if os.path.exists(pickled_optimizers_dir):
            for file_name in os.listdir(pickled_optimizers_dir):
                iteration_number, file_extension = file_name.split(".")
                assert file_extension == "pickle"
                iteration_number = int(iteration_number)
                with open(os.path.join(pickled_optimizers_dir, file_name), 'rb') as in_file:
                    optimizer_evaluation_report.pickled_optimizers_over_time[iteration_number] = in_file.read()

        objective_function_initial_state_file_path = os.path.join(target_folder, "objective_function_initial_state.pickle")
        if os.path.exists(objective_function_initial_state_file_path):
            with open(objective_function_initial_state_file_path, 'rb') as in_file:
                optimizer_evaluation_report.pickled_objective_function_initial_state = in_file.read()


        objective_function_final_state_file_path = os.path.join(target_folder, "objective_function_final_state.pickle")
        if os.path.exists(objective_function_final_state_file_path):
            with open(objective_function_final_state_file_path, 'rb') as  in_file:
                optimizer_evaluation_report.pickled_objective_function_final_state = in_file.read()

        gof_file_path = os.path.join(target_folder, "regression_model_goodness_of_fit_state.pickle")
        if os.path.exists(gof_file_path):
            with open(gof_file_path, 'rb') as in_file:
                optimizer_evaluation_report.regression_model_fit_state = pickle.load(in_file)

        optima_over_time_file_path = os.path.join(target_folder, "optima_over_time.pickle")
        if os.path.exists(optima_over_time_file_path):
            with open(optima_over_time_file_path, 'rb') as in_file:
                optimizer_evaluation_report.optima_over_time = pickle.load(in_file)

        pareto_over_time_file_path = os.path.join(target_folder, "pareto_over_time.pickle")
        if os.path.exists(pareto_over_time_file_path):
            with open(pareto_over_time_file_path, "rb") as in_file:
                optimizer_evaluation_report.pareto_over_time = pickle.load(in_file)

        pareto_volume_over_time_file_path = os.path.join(target_folder, "pareto_volume_over_time.json")
        if os.path.exists(pareto_volume_over_time_file_path):
            with open(pareto_volume_over_time_file_path, 'r') as in_file:
                optimizer_evaluation_report.pareto_volume_over_time = json.load(in_file)

        execution_info_file_path = os.path.join(target_folder, "execution_info.json")
        if os.path.exists(execution_info_file_path):
            with open(execution_info_file_path, 'r') as in_file:
                execution_info_dict = json.load(in_file)
                optimizer_evaluation_report.success = execution_info_dict['success']
                optimizer_evaluation_report.num_optimization_iterations = execution_info_dict['num_optimization_iterations']
                optimizer_evaluation_report.evaluation_frequency = execution_info_dict['evaluation_frequency']
                optimizer_evaluation_report.exception = execution_info_dict['exception']
                optimizer_evaluation_report.exception_traceback = execution_info_dict['exception_stack_trace']
                optimizer_evaluation_report.start_time = datetime.strptime(execution_info_dict['start_time'], "%d.%m.%Y.%H:%M:%S:%f")
                optimizer_evaluation_report.end_time = datetime.strptime(execution_info_dict['end_time'], "%d.%m.%Y.%H:%M:%S:%f")

        return optimizer_evaluation_report

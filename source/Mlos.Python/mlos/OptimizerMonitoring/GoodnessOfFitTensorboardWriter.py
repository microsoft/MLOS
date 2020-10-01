#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import argparse
import os
import signal
import time
from typing import Optional

import grpc
from tensorboardX import SummaryWriter # pylint: disable=wrong-import-order

from mlos.Grpc.OptimizerMonitor import OptimizerMonitor
from mlos.Optimizers.RegressionModels.RegressionModelFitState import RegressionModelFitState
from mlos.Optimizers.RegressionModels.GoodnessOfFitMetrics import GoodnessOfFitMetrics, DataSetType

class GoodnessOfFitTensorboardWriter:
    """ Queries the optimizer for goodness of fit metrics and plots them using Tensorboard.

    What we want to do is:
        1. Create a directory per optimizer.
        2. Create a subdirectory per surrogate model - one for the random forest and one for each decision tree.
        3. Create a scalar for each metric.

        The reason for all of these nested directories is that Tensorboard uses directory names to group related plots together. So writing to all those
    files helps us visualize the Goodness of Fit better.
    """

    def __init__(self, optimizer_id, grpc_port, refresh_interval_s: float = 1):
        self.keep_running = True
        self.started = False

        optimizer_monitor = OptimizerMonitor(grpc_channel=grpc.insecure_channel(f'localhost:{grpc_port}')) # pylint: disable=no-member

        if optimizer_id is None:
            existing_optimziers = optimizer_monitor.get_existing_optimizers()
            assert len(existing_optimziers) > 0
            optimizer_id = existing_optimziers[-1].id

        self.optimizer = optimizer_monitor.get_optimizer_by_id(optimizer_id=optimizer_id)


        if not self.optimizer.optimizer_config.surrogate_model_implementation == "HomogeneousRandomForestRegressionModel":
            raise NotImplementedError

        self.refresh_interval_s = refresh_interval_s
        self.top_traces_dir = os.path.join(os.path.abspath(os.getcwd()), "temp", "tensorboard", "optimizers")
        self.optimizer_traces_dir = os.path.join(self.top_traces_dir, optimizer_id)

        self.data_set_type_names = {
            DataSetType.TRAIN: "train",
            DataSetType.VALIDATION: "validation"
        }

        num_trees = self.optimizer.optimizer_config.homogeneous_random_forest_regression_model_config.n_estimators
        self.random_forest_dir = os.path.join(os.path.abspath(self.optimizer_traces_dir), self.data_set_type_names[DataSetType.TRAIN], "random_forest")
        self.decision_tree_dirs = {
            data_set_type: [
                os.path.join(os.path.abspath(self.optimizer_traces_dir), self.data_set_type_names[data_set_type], f"decision_tree_{i}")
                for i in range(num_trees)
            ]
            for data_set_type in (DataSetType.TRAIN, DataSetType.VALIDATION)
        }

        self.random_forest_writer = SummaryWriter(comment="random forest", log_dir=self.random_forest_dir)
        self.decision_tree_writers = {
            data_set_type: [SummaryWriter(comment=f"tree _{i}", log_dir=self.decision_tree_dirs[data_set_type][i]) for i in range(num_trees)]
            for data_set_type in (DataSetType.TRAIN, DataSetType.VALIDATION)
        }

        self._previous_random_forest_fit_state = None
        self._previous_decision_trees_fit_states = [None for i in range(num_trees)]

        self.column_names = GoodnessOfFitMetrics._fields

    def run(self):
        self.display_hints()
        self.started = True
        while self.keep_running:
            optimizer_convergence_state = self.optimizer.get_optimizer_convergence_state()
            random_forest_fit_state = optimizer_convergence_state.surrogate_model_fit_state
            self.emit_fit_stats(
                writer=self.random_forest_writer, current_fit_state=random_forest_fit_state,
                previous_fit_state=self._previous_random_forest_fit_state,
                data_set_type=DataSetType.TRAIN
            )

            self._previous_random_forest_fit_state = random_forest_fit_state
            for i, tree_fit_state in enumerate(random_forest_fit_state.decision_trees_fit_states):
                for data_set_type in (DataSetType.TRAIN, DataSetType.VALIDATION):
                    self.emit_fit_stats(
                        writer=self.decision_tree_writers[data_set_type][i],
                        current_fit_state=tree_fit_state,
                        previous_fit_state=self._previous_decision_trees_fit_states[i],
                        data_set_type=DataSetType.TRAIN
                    )
                self._previous_decision_trees_fit_states[i] = tree_fit_state
            if self.keep_running:
                time.sleep(self.refresh_interval_s)
        self._close_all_writers()

    def display_hints(self):
        print(f"Starting to write traces for optimizer: {self.optimizer.id}")
        print(f"To view the traces launch tensorboard using this command: ")
        print()
        print(f"\ttensorboard --logdir {self.top_traces_dir} --reload_interval 5")
        print()
        print(f"To view traces specific to this optimzier, apply the following filter:")
        print()
        print(f"\toptimizers\\\\{self.optimizer.id}\\\\.*\\\\random_forest")

    # pylint: disable=bad-continuation
    def emit_fit_stats(
        self,
        writer: SummaryWriter,
        current_fit_state: RegressionModelFitState,
        previous_fit_state: Optional[RegressionModelFitState],
        data_set_type: DataSetType
    ):
        # For now let's just do the training data set, we'll add the validation datasets later
        if previous_fit_state is not None:
            previous_num_records = len(previous_fit_state.historical_gof_metrics[data_set_type])
        else:
            previous_num_records = 0
        new_records = current_fit_state.historical_gof_metrics[data_set_type][previous_num_records:]
        for gof_record in new_records:
            iteration_number = gof_record._asdict()['last_refit_iteration_number']
            for i, col_name in enumerate(self.column_names):
                if col_name in ("last_refit_iteration_number", "prediction_count", "data_set_type", "observation_count"):
                    continue
                writer.add_scalar(tag=col_name, scalar_value=gof_record[i], global_step=iteration_number)
        writer.flush()

    def _close_all_writers(self):
        self.random_forest_writer.flush()
        self.random_forest_writer.close()

        for _, decision_tree_writers in self.decision_tree_writers.items():
            for writer in decision_tree_writers:
                writer.flush()
                writer.close()

def parse_command_line_arguments():
    parser = argparse.ArgumentParser(prog="Goodness of Fit Tensorboard Writer")
    subparsers_factory = parser.add_subparsers(
        dest="command",
        help="Use the launch command to start the tensorboard writer process."
    )

    launch_subcommand_parser = subparsers_factory.add_parser("launch", help="Launch the writer.")
    launch_subcommand_parser.add_argument('--port', type=int, required=False, default=50051, help="gRPC port.")
    launch_subcommand_parser.add_argument('--optimizer-id', type=str, required=False, default=None,
                                          help="Id of optimizer to start monitoring. If not specified the monitor will connect to the newest optimizer.")

    arguments = parser.parse_args()
    assert 0 < arguments.port < 65535, "Port must be an integer between 0 and 65535"
    return arguments


def ctrl_c_handler(_, __):
    print("Received CTRL-C: shutting down.")
    if gof_tensorboard_writer.started:
        print("Shutting down server.")
        gof_tensorboard_writer.keep_running = False
        print("Server stopped.")


if __name__ == "__main__":
    signal.signal(signal.SIGINT, ctrl_c_handler)
    args = parse_command_line_arguments()
    gof_tensorboard_writer = GoodnessOfFitTensorboardWriter(optimizer_id=args.optimizer_id, grpc_port=args.port)
    gof_tensorboard_writer.run()

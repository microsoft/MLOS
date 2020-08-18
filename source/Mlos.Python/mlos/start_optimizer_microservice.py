#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
""" Launches the mlos Optimizer gRPC service.

The difference between this and start_mlos_optimization_runtime.py is that we are using
gRPC and BayesianOptimizer here, whereas we are using SqlRPC and bayes_opt there. In other
words, this script is meant to supersede the start_mlos_optimization_runtime.py.
"""
import argparse
import signal

from mlos.Grpc.OptimizerMicroserviceServer import OptimizerMicroserviceServer
import mlos.global_values as global_values


def parse_command_line_arguments():
    parser = argparse.ArgumentParser(prog="mlos Optimizer Microservice")
    subparsers_factory = parser.add_subparsers(
        dest="command",
        help="Use an appropriate sub-command to launch the mlos Optimizer Microservice"
    )

    launch_subcommand_parser = subparsers_factory.add_parser("launch", help="Launch mlos Optimizer Microservice.")
    launch_subcommand_parser.add_argument('--port', type=int, required=False, default=50051,
                                          help="gRPC port.")
    launch_subcommand_parser.add_argument('--num-threads', type=int, required=False, default=10,
                                          help="Maximum number of threads to service gRPC requests.")
    arguments = parser.parse_args()
    assert arguments.port > 0, "Port must be a positive integer." # TODO: enforce the upper limit too.
    assert arguments.num_threads > 0, "Number of threads must be a positive integer."
    return arguments


def ctrl_c_handler(_, __):
    print("Received CTRL-C: shutting down.")
    if server.started:
        print("Shutting down server.")
        server.stop(grace=None)
        print("Server stopped.")


if __name__ == "__main__":
    global_values.declare_singletons()
    signal.signal(signal.SIGINT, ctrl_c_handler)
    args = parse_command_line_arguments()
    server = OptimizerMicroserviceServer(port=args.port, num_threads=args.num_threads)
    server.start()
    server.wait_for_termination()

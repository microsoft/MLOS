#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
""" Launches the mlos Optimizer gRPC service.
"""
import argparse
import signal

from mlos.Grpc.OptimizerServicesServer import OptimizerServicesServer
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


def main():
    args = parse_command_line_arguments()
    server = OptimizerServicesServer(port=args.port, num_threads=args.num_threads)

    def ctrl_c_handler(_, __):
        print("Received CTRL-C: shutting down.")
        if server.started:
            print("Shutting down server.")
            server.stop(grace=None)
            print("Server stopped.")

    global_values.declare_singletons()
    signal.signal(signal.SIGINT, ctrl_c_handler)
    signal.signal(signal.SIGTERM, ctrl_c_handler)
    print("Starting Optimizer Microservice ...")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    main()

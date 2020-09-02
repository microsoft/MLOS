#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import argparse

from .MlosOptimizationServices.MlosOptimizationRuntime import MlosOptimizationRuntime
from .MlosOptimizationServices.ModelsDatabase.ConnectionString import ConnectionString

def parse_command_line_arguments():
    parser = argparse.ArgumentParser(prog="Mlos Model Services")
    subparsers_factory = parser.add_subparsers(
        dest="command",
        help="Use an appropriate sub-command to launch the Mlos Model Services."
    )

    launch_subcommand_parser = subparsers_factory.add_parser('launch', help='Launch Mlos Model Services')
    launch_subcommand_parser.add_argument('--database-connection-string-file', type=str, required=True,
                                          help="Path to a json specifying database connection string details.")

    init_db_subcommand_parser = subparsers_factory.add_parser('init-db', help='Initialize the ModelsDatabase')
    init_db_subcommand_parser.add_argument('--database-connection-string-file', type=str, required=True,
                                           help="Path to a json specifying database connection string details.")

    arguments = parser.parse_args()
    return arguments

def main():
    from . import global_values
    global_values.declare_singletons()
    global_values.rpc_handlers = dict()

    from .Optimizers.DistributableSimpleBayesianOptimizer import DistributableSimpleBayesianOptimizer

    args = parse_command_line_arguments()
    connection_string = ConnectionString.create_from_config_file(config_file_path=args.database_connection_string_file)
    mlos_model_runtime = MlosOptimizationRuntime(models_database_connection_string=connection_string)

    if args.command == "launch":
        print("Launching MLOS model runtime ...")
        mlos_model_runtime.add_distributable_class(DistributableSimpleBayesianOptimizer)
        mlos_model_runtime.register_global_rpc_handlers()
        mlos_model_runtime.run()

    elif args.command == "init-db":
        print("Initializing MLOS database")
        mlos_model_runtime.initialize_database()


if __name__ == "__main__":
    main()

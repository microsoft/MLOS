#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import json
import time

from mlos import global_values
from mlos.global_values import serialize_to_bytes_string

from mlos.Logger import create_logger
from mlos.Spaces.HypergridsJsonEncoderDecoder import HypergridJsonEncoder, HypergridJsonDecoder

from .ModelsDatabase.ModelsDatabase import ModelsDatabase

class MlosOptimizationRuntime:
    """ Instantiates optimizers and models to satisfy requests submitted to MlosOptimizationServices.

    """

    def __init__(self, models_database_connection_string, logger=None):
        self.logger = logger if logger is not None else create_logger("MlosOptimizationRuntime")
        self.models_database = ModelsDatabase(
            connection_string=models_database_connection_string,
            logger=self.logger
        )
        self.distributable_classes = dict()
        self.rpc_handlers = dict()
        self.execution_context_cache = dict()

    def add_distributable_class(self, class_object):
        self.distributable_classes[class_object.__name__] = class_object

    def register_global_rpc_handlers(self):
        for rpc_function_name, _ in global_values.rpc_handlers.items():
            class_name, function_name = rpc_function_name.split(".")
            class_object = self.distributable_classes.get(class_name, None)
            if class_object is None:
                continue
            self.add_rpc_handler(rpc_function_name, class_object, function_name)

    def add_rpc_handler(self, rpc_name, optimizer_class, method_name):
        self.rpc_handlers[rpc_name] = (optimizer_class, method_name)

    @property
    def check_for_work_interval_milliseconds(self):
        # TODO: make this an intelligent choice
        return 100

    # pylint: disable=no-self-use
    def keep_running(self):
        # TODO: emit heartbeat, check if we are supposed to stop
        return True

    def initialize_database(self):
        self.logger.info("Initializing database.")
        self.models_database.drop_target_database()
        self.models_database.create_target_database()
        self.models_database.create_database_schema()

    def run(self):
        """ Continuously queries the database for work and satisfies the requests as they trickle in.

        NOTE: this is a v0 naive implementation to get the scenarios working E2E. Lot's of optimizations
        are possible here - chiefly in the areas of multiprocessing and caching.
        :return:
        """

        while self.keep_running():
            rpc_to_complete = self.models_database.get_rpc_to_complete(allowed_rpc_names=self.rpc_handlers.keys())

            if rpc_to_complete is None:
                # Nothing to do... let's chill for a bit
                time.sleep(self.check_for_work_interval_milliseconds / 1000.0)
                continue

            self.complete_rpc(rpc_to_complete)

    def complete_rpc(self, rpc):
        try:
            optimizer_class, function_name = self.rpc_handlers[rpc.remote_procedure_name]
            execution_context = json.loads(rpc.execution_context, cls=HypergridJsonDecoder)
            optimizer_instance = self.execution_context_cache.get((execution_context["optimizer_id"], execution_context['model_versions'][0]), None)
            if optimizer_instance is None:
                optimizer_instance = optimizer_class.restore_from_execution_context(execution_context, self.models_database)
                self.execution_context_cache[(execution_context["optimizer_id"], execution_context['model_versions'][0])] = optimizer_instance
            method_to_call = getattr(optimizer_instance, function_name)
            kwargs = json.loads(rpc.arguments, cls=HypergridJsonDecoder)
            result = method_to_call(**kwargs)
            rpc.result = json.dumps(result, cls=HypergridJsonEncoder)
            rpc.request_status = 'complete'
            self.models_database.complete_rpc(rpc)

        except Exception as e:
            # TODO: check if exception should be propagated
            self.logger.error("Failed to execute rpc.", exc_info=True)
            rpc.result = serialize_to_bytes_string(e)
            rpc.request_status = 'failed'
            rpc.expected_current_status = 'in progress'
            self.models_database.update_rpc_request_status(rpc)

#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from functools import wraps
import json

from mlos import global_values
from mlos.Spaces.HypergridsJsonEncoderDecoder import HypergridJsonEncoder

from .ModelsDatabase.Relations.RemoteProcedureCall import RemoteProcedureCall

def remotely_executable(timeout_s=120):
    """ Allows a function to execute remotely.

    :return:
    """

    def decorator(wrapped_function):

        if hasattr(global_values, 'rpc_handlers') and global_values.rpc_handlers is not None:
            # pylint: disable=unsupported-assignment-operation
            global_values.rpc_handlers[wrapped_function.__qualname__] = wrapped_function

        @wraps(wrapped_function)
        def wrapper(*args, **kwargs):
            assert len(args) == 1, "Remotely executable functions must be called with json-serializable key-word arguments only."
            self = args[0]

            if not self.execute_remotely:
                return wrapped_function(*args, **kwargs)

            rpc = RemoteProcedureCall(
                remote_procedure_name=wrapped_function.__qualname__,
                execution_context=json.dumps(self.get_execution_context(), cls=HypergridJsonEncoder),
                arguments=json.dumps(kwargs, cls=HypergridJsonEncoder)
            )
            return global_values.ml_model_services_proxy.execute_rpc(rpc, timeout_s=timeout_s)
        return wrapper
    return decorator

class Distributable:
    """ Defines an interface for all classes that support remote execution.

    """

    remotely_executable_methods = {}

    def __init__(self, execute_remotely=False):
        self.execute_remotely = execute_remotely

    def get_execution_context(self):
        raise NotImplementedError("All subclasses must implement this.")

    @classmethod
    def restore_from_execution_context(cls, execution_context, models_database=None):
        raise NotImplementedError("All subclasses must implement this.")

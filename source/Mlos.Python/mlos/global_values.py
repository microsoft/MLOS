#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import codecs
import pickle


def declare_singletons():
    """ This is a workaround to overcome Python's default 'import' behavior.

    What one would expect is to simply declare a single global value in this file like ml_model_services_proxy
    initialize it to a singleton class and import it into each file.

    The problem is that calling from global_values import ml_model_services would actually invoke the
    initializer on every import, so every importing module would have a copy of what was meant to be a
    singleton class.

    The solution is to have this file, and call init() only once per process, followed by the construction
    of each of the singletons. Then each module that imports the global_values.py will have access to all
    singletons as you would expect.

    Example usage:

    # in file main_program.py

    import mlos.global_values as global_values
    import all_the_other_stuff_you_need

    if __name__ == "__main__":
        global_values.declare_singletons()  # This creates globals: ml_model_services_proxy, rpc_handlers, and tracer
        global_values.ml_model_services_proxy = MLModelServicesProxy(...)
        global_values.rpc_handlers = dict()
        global_values.tracer = Tracer(...)

    ###############################################################################################

    # in any other file that needs any of the singletons
    import global_values

    global_values.tracer.clear_events() # Or any other API

    :return:
    """

    global ml_model_services_proxy  # pylint: disable=global-variable-undefined
    global rpc_handlers  # pylint: disable=global-variable-undefined
    global tracer  # pylint: disable=global-variable-undefined

    ml_model_services_proxy = None
    rpc_handlers = None
    tracer = None

def serialize_to_bytes_string(obj):
    return codecs.encode(pickle.dumps(obj), "base64").decode()

def deserialize_from_bytes_string(bytes_string):
    return pickle.loads(codecs.decode(bytes_string.encode(), "base64"))

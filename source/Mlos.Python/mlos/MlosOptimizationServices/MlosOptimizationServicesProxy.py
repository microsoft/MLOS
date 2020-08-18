#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import datetime
import json
import time

from mlos.global_values import deserialize_from_bytes_string
from mlos.Logger import create_logger
from mlos.Spaces.HypergridsJsonEncoderDecoder import HypergridJsonDecoder

from .ModelsDatabase.ModelsDatabase import ModelsDatabase
from .ModelsDatabase.Relations.RemoteProcedureCall import RemoteProcedureCall


class MlosOptimizationServicesProxy:
    """ An interface to MlosOptimizationServices

    """

    def __init__(self, models_database_connection_string, logger=None):
        self.logger = logger if logger is not None else create_logger("MLModelServicesProxy")
        self.models_database = ModelsDatabase(
            connection_string=models_database_connection_string,
            logger=self.logger
        )

    def execute_rpc(self, rpc: RemoteProcedureCall, timeout_s: float = 120):
        timeout_period_end = datetime.datetime.utcnow() + datetime.timedelta(seconds=timeout_s)
        spin_interval_ms = 10 # TODO: make intelligent choice

        submitted_rpc = self.models_database.submit_remote_procedure_call(rpc=rpc)
        old_status = submitted_rpc.request_status
        while datetime.datetime.now() < timeout_period_end:
            self.models_database.get_updated_request_status(submitted_rpc)
            if submitted_rpc.request_status != old_status:
                if submitted_rpc.request_status == 'complete':
                    #self.models_database.remove_rpc(submitted_rpc)
                    return json.loads(submitted_rpc.result, cls=HypergridJsonDecoder)
                if submitted_rpc.request_status == 'in progress':
                    continue
                if submitted_rpc.request_status == 'failed':
                    if submitted_rpc.result is not None:
                        exception = deserialize_from_bytes_string(rpc.result)
                        raise exception
                else:
                    raise RuntimeError(f"Remote Procedure Call status: {submitted_rpc.request_status}.")
            else:
                # nothing to do... chill for a bit
                time.sleep(spin_interval_ms / 1000.0)
        submitted_rpc.status = 'timed out'
        self.models_database.get_updated_request_status(submitted_rpc)
        raise TimeoutError("Remote Procedure Call timed out.")

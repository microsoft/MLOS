# pylint: disable=no-member
#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from concurrent.futures import ThreadPoolExecutor

import grpc

from mlos.Grpc import OptimizerService_pb2_grpc
from mlos.Grpc.OptimizerMicroservice import OptimizerMicroservice
from mlos.Logger import create_logger



class OptimizerMicroserviceServer:
    """ Hosts the OptimizerMicroservice.

    The functionality to stand up the gRPC server is needed in unit tests (in process)
    as well as in the 'start_optimizer_microservice.py' launcher script. Both of them
    should instantiate an object of this class to achieve that.
    """

    def __init__(self, port, num_threads=10):
        self.port = port
        self.num_threads = num_threads
        self.started = False
        self._server = None
        self.logger = create_logger("OptimizerMicroserviceServer init")


    def start(self):
        assert self._server is None, "Server already started"
        self._server = grpc.server(ThreadPoolExecutor(max_workers=self.num_threads))
        OptimizerService_pb2_grpc.add_OptimizerServiceServicer_to_server(
            OptimizerMicroservice(),
            self._server
        )
        self._server.add_insecure_port(f'[::]:{self.port}')
        self._server.start()
        self.started = True
        self.logger.info("OptimizerMicroserviceServer started")

    def stop(self, grace=None):
        self._server.stop(grace=grace)
        self.logger.info("OptimizerMicroserviceServer stopped")


    def wait_for_termination(self, timeout=None):
        if self.started:
            self._server.wait_for_termination(timeout=timeout)

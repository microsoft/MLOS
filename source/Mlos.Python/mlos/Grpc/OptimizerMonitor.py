#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from mlos.Grpc.OptimizerMonitoringService_pb2_grpc import OptimizerMonitoringServiceStub
from mlos.Grpc.OptimizerMonitoringService_pb2 import Empty, OptimizerHandle
from mlos.Optimizers.BayesianOptimizerFactory import BayesianOptimizerFactory
from mlos.Logger import create_logger


class OptimizerMonitor:
    """Enables monitoring optimizers existing within the OptimizerMicroservice.

    """

    def __init__(self, grpc_channel, logger=None):
        self.logger = logger if logger is not None else create_logger("OptimizerMonitor")
        self._grpc_channel = grpc_channel
        self._optimizer_monitoring_stub = OptimizerMonitoringServiceStub(channel=self._grpc_channel)
        self._optimizer_factory = BayesianOptimizerFactory(grpc_channel=self._grpc_channel, logger=self.logger)

    def __repr__(self):
        return f"OptimizerMonitor(grpc_channel='{self._grpc_channel._channel.target().decode()}')"  # pylint: disable=protected-access

    def get_existing_optimizers(self):
        """Returns proxies to all existing optimizers.

        :return:
        """
        request = Empty()
        optimizer_list = self._optimizer_monitoring_stub.ListExistingOptimizers(request)

        optimizer_proxies = [
            self._optimizer_factory.connect_to_existing_remote_optimizer(optimizer_info)
            for optimizer_info
            in optimizer_list.Optimizers
        ]
        return optimizer_proxies

    def get_optimizer_by_id(self, optimizer_id):
        """Returns a proxy to an optimizer with a specified Id.

        :param optimizer_id:
        :return:
        """
        optimizer_handle = OptimizerHandle(Id=optimizer_id)
        optimizer_info = self._optimizer_monitoring_stub.GetOptimizerInfo(optimizer_handle)
        optimizer_proxy = self._optimizer_factory.connect_to_existing_remote_optimizer(optimizer_info)
        return optimizer_proxy

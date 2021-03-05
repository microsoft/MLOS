#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from mlos.Logger import create_logger

from mlos.Grpc.OptimizerService_pb2 import CreateOptimizerRequest, OptimizerInfo
from mlos.Grpc.OptimizerService_pb2_grpc import OptimizerServiceStub
from mlos.Grpc.BayesianOptimizerProxy import BayesianOptimizerProxy
from mlos.Optimizers.BayesianOptimizer import BayesianOptimizer, bayesian_optimizer_config_store
from mlos.Optimizers.OptimizationProblem import OptimizationProblem
from mlos.Spaces import Point


class BayesianOptimizerFactory:
    """Produces BayesianOptimizerProxies either by connecting them to either a new or an existing remote bayesian optimizer.

    Parameters
    ----------
    grpc_channel : int
        Port for the grpc communication channel.

    logger : Logger
        Logger object
    """

    def __init__(self, grpc_channel=None, logger=None):
        self.logger = logger if logger is not None else create_logger("BayesianOptimizerFactory")
        self._grpc_channel = grpc_channel
        self._optimizer_service_stub = None
        if self._grpc_channel is not None:
            self._optimizer_service_stub = OptimizerServiceStub(channel=self._grpc_channel)


    def create_local_optimizer(self, optimization_problem: OptimizationProblem, optimizer_config: Point = None) -> BayesianOptimizer:
        if optimizer_config is None:
            self.logger.info(f"Optimizer config not specified. Using default.")
            optimizer_config = bayesian_optimizer_config_store.default

        self.logger.info(f"Creating a bayesian optimizer with config: {optimizer_config.to_json(indent=2)}.")

        return BayesianOptimizer(
            optimization_problem=optimization_problem,
            optimizer_config=optimizer_config,
            logger=self.logger
        )


    def create_remote_optimizer(self, optimization_problem: OptimizationProblem, optimizer_config: Point = None) -> BayesianOptimizerProxy:
        """Creates a remote optimizer over a given problem with a given config.

        Parameters
        ----------
        optimization_problem : OptimizationProblem
            Optimization problem for the new remote optimizer.

        optimizer_config : Point
            Configuration for the new remote optimizer.


        Returns
        -------
        BayesianOptimizerProxy

        """
        assert self._optimizer_service_stub is not None

        if optimizer_config is None:
            optimizer_config = bayesian_optimizer_config_store.default

        create_optimizer_request = CreateOptimizerRequest(
            OptimizationProblem=optimization_problem.to_protobuf(),
            OptimizerConfigName='', # TODO: add this functionality
            OptimizerConfig=optimizer_config.to_json()
        )

        self.logger.info(f"Creating a remote bayesian optimizer with config: {optimizer_config.to_json(indent=2)}.")

        optimizer_handle = self._optimizer_service_stub.CreateOptimizer(create_optimizer_request)

        return BayesianOptimizerProxy(
            grpc_channel=self._grpc_channel,
            optimization_problem=optimization_problem,
            optimizer_config=optimizer_config,
            id=optimizer_handle.Id,
            logger=self.logger
        )

    def connect_to_existing_remote_optimizer(self, optimizer_info: OptimizerInfo) -> BayesianOptimizerProxy:
        """Connects to an existing optimizer.

        Parameters
        ----------
        optimizer_info : OptimizerInfo

        Returns
        -------
        BayesianOptimizerProxy
        """
        return BayesianOptimizerProxy(
            grpc_channel=self._grpc_channel,
            optimization_problem=OptimizationProblem.from_protobuf(optimizer_info.OptimizationProblem),
            optimizer_config=Point.from_json(optimizer_info.OptimizerConfigJsonString),
            id=optimizer_info.OptimizerHandle.Id,
            logger=self.logger
        )

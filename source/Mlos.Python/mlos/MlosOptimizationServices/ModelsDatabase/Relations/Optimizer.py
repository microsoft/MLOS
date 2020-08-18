#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
class Optimizer:
    """ An instance of optimizer in the ModelsDatabase

    """
    def __init__(
            self,
            optimizer_id=None,
            optimizer_type=None,
            optimizer_config=None,
            optimizer_hypergrid=None,
            optimizer_focused_hypergrid=None,
            optimization_problem=None,
            models=None,
            registered_params_combos=None
    ):
        self.optimizer_id = optimizer_id
        self.optimizer_type = optimizer_type
        self.optimizer_config = optimizer_config
        self.optimizer_hypergrid = optimizer_hypergrid
        self.optimizer_focused_hypergrid = optimizer_focused_hypergrid
        self.optimization_problem = optimization_problem
        self.models = models if models is not None else []
        self.registered_params_combos = registered_params_combos

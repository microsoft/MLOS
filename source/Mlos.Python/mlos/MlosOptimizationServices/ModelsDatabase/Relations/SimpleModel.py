#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
class SimpleModel:
    """ An instance of simple model in ModelsDatabase

    """

    def __init__(
            self,
            optimizer_id=None,
            model_id=None,
            model_type=None,
            model_config=None,
            model_version=None,
            model_hypergrid=None,
            serialized_model=None
    ):
        self.optimizer_id = optimizer_id
        self.model_id = model_id
        self.model_type = model_type
        self.model_config = model_config
        self.model_version = model_version
        self.model_hypergrid = model_hypergrid
        self.serialized_model = serialized_model

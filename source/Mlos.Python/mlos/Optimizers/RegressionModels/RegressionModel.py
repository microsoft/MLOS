#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from abc import ABC, abstractmethod


class RegressionModel(ABC):
    """ An abstract class for all regression models to implement.

    The purpose of this class is to indicate the type and configuration of the regression model
    so that all models can be inspected in a homogeneous way.
    """

    @abstractmethod
    def __init__(self, model_type, model_config):
        self.model_type = model_type
        self.model_config = model_config
        super().__init__()

class RegressionModelConfig(ABC):
    """ An abstract class for all regression models config to implement.

    """

    @classmethod
    @abstractmethod
    def contains(cls, config):
        """

        :param config:
        :return:
        """
        raise NotImplementedError

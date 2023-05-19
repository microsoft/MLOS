#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Contains the wrapper class for Emukit Bayesian optimizers.
"""

from typing import Callable, Optional

import ConfigSpace
import numpy as np
import numpy.typing as npt
import pandas as pd

from mlos_core.optimizers.bayesian_optimizers.bayesian_optimizer import BaseBayesianOptimizer

from mlos_core.spaces.adapters.adapter import BaseSpaceAdapter
from mlos_core.spaces import configspace_to_skopt_space


class SkoptOptimizer(BaseBayesianOptimizer):
    """Wrapper class for Skopt based Bayesian optimization.

    Parameters
    ----------
    parameter_space : ConfigSpace.ConfigurationSpace
        The parameter space to optimize.
    """

    def __init__(self, *,
                 parameter_space: ConfigSpace.ConfigurationSpace,
                 space_adapter: Optional[BaseSpaceAdapter] = None,
                 base_estimator: str = 'gp',
                 seed: Optional[int] = None):

        super().__init__(
            parameter_space=parameter_space,
            space_adapter=space_adapter,
        )

        from skopt import Optimizer as Optimizer_Skopt  # pylint: disable=import-outside-toplevel
        self.base_optimizer = Optimizer_Skopt(
            configspace_to_skopt_space(self.optimizer_parameter_space),
            base_estimator=base_estimator,
            random_state=seed,
        )
        self._transform: Callable[[pd.DataFrame], npt.NDArray]
        if base_estimator == 'et':
            self._transform = self._to_1hot
        elif base_estimator == 'gp':
            self._transform = self._to_numeric
        else:
            self._transform = pd.DataFrame.to_numpy

    def _to_numeric(self, config: pd.DataFrame) -> npt.NDArray:
        """
        Convert categorical values in the DataFrame to ordinal integers and return a numpy array.
        This transformation is necessary for the Gaussian Process based optimizer.

        Parameters
        ----------
        config : pd.DataFrame
            Dataframe of configurations / parameters.
            The columns are parameter names and the rows are the configurations.

        Returns
        -------
        config : np.array
            Numpy array of floats with all categoricals replaced with their ordinal numbers.
        """
        config = config.copy()
        for param in self.optimizer_parameter_space.get_hyperparameters():
            if isinstance(param, ConfigSpace.CategoricalHyperparameter):
                config[param.name] = config[param.name].apply(param.choices.index)
        return config.to_numpy(dtype=np.float32)

    def _register(self, configurations: pd.DataFrame, scores: pd.Series,
                  context: Optional[pd.DataFrame] = None) -> None:
        """Registers the given configurations and scores.

        Parameters
        ----------
        configurations : pd.DataFrame
            Dataframe of configurations / parameters. The columns are parameter names and the rows are the configurations.

        scores : pd.Series
            Scores from running the configurations. The index is the same as the index of the configurations.

        context : pd.DataFrame
            Not Yet Implemented.
        """
        if context is not None:
            raise NotImplementedError()
        # DataFrame columns must be in the same order
        # as the hyperparameters in the config space:
        param_names = self.optimizer_parameter_space.get_hyperparameter_names()
        data = configurations[param_names].to_numpy().tolist()
        self.base_optimizer.tell(data, scores.to_list())

    def _suggest(self, context: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """Suggests a new configuration.

        Parameters
        ----------
        context : pd.DataFrame
            Not Yet Implemented.

        Returns
        -------
        configuration : pd.DataFrame
            Pandas dataframe with a single row. Column names are the parameter names.
        """
        if context is not None:
            raise NotImplementedError("Scikit-optimize does not support context yet.")
        return pd.DataFrame([self.base_optimizer.ask()], columns=self.optimizer_parameter_space.get_hyperparameter_names())

    def register_pending(self, configurations: pd.DataFrame,
                         context: Optional[pd.DataFrame] = None) -> None:
        raise NotImplementedError("Not supported in scikit-optimize.")

    def surrogate_predict(self, configurations: pd.DataFrame, context: Optional[pd.DataFrame] = None) -> npt.NDArray:
        if context is not None:
            raise NotImplementedError("Scikit-optimize does not support context yet.")
        if self.space_adapter is not None:
            raise NotImplementedError("Scikit-optimize does not support space adapters yet.")
        ret: npt.NDArray = self.base_optimizer.models[-1].predict(self._transform(configurations))
        return ret

    def acquisition_function(self, configurations: pd.DataFrame,
                             context: Optional[pd.DataFrame] = None) -> npt.NDArray:
        # This seems actually non-trivial to get out of skopt, so maybe we actually shouldn't implement this.
        raise NotImplementedError("Not supported in scikit-optimize.")

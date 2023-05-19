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
from mlos_core.spaces import configspace_to_emukit_space


class EmukitOptimizer(BaseBayesianOptimizer):
    """Wrapper class for Emukit based Bayesian optimization.

    Parameters
    ----------
    parameter_space : ConfigSpace.ConfigurationSpace
        The parameter space to optimize.

    space_adapter : BaseSpaceAdapter
        The space adapter class to employ for parameter space transformations.
    """

    def __init__(self, *,
                 parameter_space: ConfigSpace.ConfigurationSpace,
                 space_adapter: Optional[BaseSpaceAdapter] = None):

        super().__init__(
            parameter_space=parameter_space,
            space_adapter=space_adapter,
        )

        # pylint: disable=import-outside-toplevel
        from emukit.examples.gp_bayesian_optimization.single_objective_bayesian_optimization import GPBayesianOptimization
        self.emukit_parameter_space = configspace_to_emukit_space(self.optimizer_parameter_space)
        self.gpbo: GPBayesianOptimization

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
        from emukit.core.loop.user_function_result import UserFunctionResult    # pylint: disable=import-outside-toplevel
        if context is not None:
            # not sure how that works here?
            raise NotImplementedError()
        if getattr(self, 'gpbo', None) is None:
            # we're in the random initialization phase
            # just remembering the observation above is enough
            return
        results = []
        for (_, config), score in zip(configurations.iterrows(), scores):
            one_hot = self._to_1hot(pd.DataFrame([config]))
            results.append(UserFunctionResult(one_hot[0], np.array([score])))
        self.gpbo.loop_state.update(results)
        self.gpbo._update_models()  # pylint: disable=protected-access

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
            raise NotImplementedError()
        if len(self._observations) <= 10:
            from emukit.core.initial_designs import RandomDesign    # pylint: disable=import-outside-toplevel
            config = RandomDesign(self.emukit_parameter_space).get_samples(1)
        else:
            if getattr(self, 'gpbo', None) is None:
                # this should happen exactly once, when calling the 11th time
                self._initialize_optimizer()
            # this should happen any time after the initial model is created
            config = self.gpbo.get_next_points(results=[])
        return self._from_1hot(config)

    def register_pending(self, configurations: pd.DataFrame,
                         context: Optional[pd.DataFrame] = None) -> None:
        raise NotImplementedError("Not implemented for EmuKit yet.")

    def surrogate_predict(self, configurations: pd.DataFrame,
                          context: Optional[pd.DataFrame] = None) -> npt.NDArray:
        if context is not None:
            raise NotImplementedError("EmuKit does not support context yet.")
        if self.space_adapter is not None:
            raise NotImplementedError("EmuKit does not support space adapters yet.")
        if self._space_adapter:
            configurations = self._space_adapter.inverse_transform(configurations)
        one_hot = self._to_1hot(configurations)
        # TODO return variance in some way
        mean_predictions, _variance_predictions = self.gpbo.model.predict(one_hot)
        # make 2ndim array into column vector
        ret: npt.NDArray = mean_predictions.reshape(-1,)
        return ret

    def acquisition_function(self, configurations: pd.DataFrame,
                             context: Optional[pd.DataFrame] = None) -> Callable:
        raise NotImplementedError("Not implemented for EmuKit yet.")

    def _initialize_optimizer(self) -> None:
        """Bootstrap a new Emukit optimizer on the initial observations."""
        from emukit.examples.gp_bayesian_optimization.single_objective_bayesian_optimization import GPBayesianOptimization  # noqa pylint: disable=import-outside-toplevel
        observations = self.get_observations()

        initial_input = observations.drop(columns='score')
        initial_output = observations[['score']]

        if self.space_adapter is not None:
            initial_input = self.space_adapter.inverse_transform(initial_input)

        self.gpbo = GPBayesianOptimization(
            variables_list=self.emukit_parameter_space.parameters,
            X=self._to_1hot(initial_input),
            Y=np.array(initial_output)
        )

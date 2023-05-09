#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Contains the wrapper class for SMAC Bayesian optimizers.
"""

from pathlib import Path
from typing import Mapping, Optional

import ConfigSpace
import numpy.typing as npt
import pandas as pd

from mlos_core.optimizers.bayesian_optimizers import BaseBayesianOptimizer
from mlos_core.spaces.adapters.adapter import BaseSpaceAdapter


class SmacOptimizer(BaseBayesianOptimizer):
    """ Wrapper class for SMAC based Bayesian optimization.

    Parameters
    ----------
    parameter_space : ConfigSpace.ConfigurationSpace
        The parameter space to optimize.
    """
    def __init__(
        self,
        parameter_space: ConfigSpace.ConfigurationSpace,
        space_adapter: Optional[BaseSpaceAdapter] = None,
        seed: Optional[int] = None,
        run_name: str = 'smac',
        output_directory: str = 'smac3_output',
        n_random_init: Optional[int] = 10,
        n_random_probability: Optional[float] = 0.1,
        n_workers: int = 1,
    ):
        super().__init__(parameter_space, space_adapter)

        from smac import HyperparameterOptimizationFacade as Optimizer_Smac # pylint: disable=import-outside-toplevel
        from smac import Scenario # pylint: disable=import-outside-toplevel
        from smac.intensifier.abstract_intensifier import AbstractIntensifier # pylint: disable=import-outside-toplevel
        from smac.initial_design import LatinHypercubeInitialDesign # pylint: disable=import-outside-toplevel
        from smac.main.config_selector import ConfigSelector # pylint: disable=import-outside-toplevel
        from smac.random_design.probability_design import ProbabilityRandomDesign # pylint: disable=import-outside-toplevel
        from smac.runhistory import TrialInfo # pylint: disable=import-outside-toplevel

        self.trial_info_map: Mapping[ConfigSpace.Configuration, TrialInfo] = {} # Stores TrialInfo instances returned by .ask()

        # Instantiate Scenario
        output_directory = Path(output_directory)
        scenario: Scenario = Scenario(
            self.optimizer_parameter_space,
            name=run_name,
            output_directory=output_directory,
            deterministic=True,
            n_trials=1e4,
            seed=seed or -1, # if -1, SMAC will generate a random seed internally
            n_workers=n_workers,
        )
        intensifier: AbstractIntensifier = Optimizer_Smac.get_intensifier(scenario, max_config_calls=1)
        config_selector: ConfigSelector = ConfigSelector(scenario, retrain_after=1)

        # Customize SMAC's randomized behavior
        initial_design: Optional[LatinHypercubeInitialDesign] = None
        if n_random_init is not None:
            initial_design = LatinHypercubeInitialDesign(scenario=scenario, n_configs=n_random_init)
        random_design: Optional[ProbabilityRandomDesign] = None
        if n_random_probability is not None:
            random_design = ProbabilityRandomDesign(probability=n_random_probability)

        # Create SMAC optimizer
        self.base_optimizer = Optimizer_Smac(
            scenario,
            SmacOptimizer._dummy_target_func,
            initial_design=initial_design,
            intensifier=intensifier,
            random_design=random_design,
            config_selector=config_selector,
            overwrite=True,
        )

    @staticmethod
    def _dummy_target_func(seed):
        """Dummy target function for SMAC optimizer.

        Since we only use the ask-and-tell interface, this is never called.
        """
        # NOTE: Providing a target function when using the ask-and-tell interface is an imperfection of the API
        # -- this planned to be fixed in some future release: https://github.com/automl/SMAC3/issues/946
        raise RuntimeError('This function should never be called.')

    def _register(self, configurations: pd.DataFrame, scores: pd.Series, context: Optional[pd.DataFrame] = None) -> None:
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
        from smac.runhistory import StatusType, TrialInfo, TrialValue   # pylint: disable=import-outside-toplevel

        if context is not None:
            raise NotImplementedError()

        # Register each trial (one-by-one)
        for config, score in zip(self._to_configspace_configs(configurations), scores.tolist()):
            # Retrieve previously generated TrialInfo (returned by .ask()) or create new TrialInfo instance
            info: TrialInfo = self.trial_info_map.get(config, TrialInfo(config=config))
            value: TrialValue = TrialValue(cost=score, time=0.0, status=StatusType.SUCCESS)
            self.base_optimizer.tell(info, value, save=False)

        # Save optimizer once we register all configs
        self.base_optimizer.optimizer.save()

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
        from smac.runhistory import TrialInfo # pylint: disable=import-outside-toplevel

        if context is not None:
            raise NotImplementedError()

        trial: TrialInfo = self.base_optimizer.ask()
        self.trial_info_map[trial.config] = trial
        return pd.DataFrame([trial.config], columns=self.optimizer_parameter_space.get_hyperparameter_names())

    def register_pending(self, configurations: pd.DataFrame, context: Optional[pd.DataFrame] = None) -> None:
        raise NotImplementedError()

    def surrogate_predict(self, configurations: pd.DataFrame, context: Optional[pd.DataFrame] = None) -> npt.NDArray:
        from smac.utils.configspace import convert_configurations_to_array  # pylint: disable=import-outside-toplevel

        if context is not None:
            raise NotImplementedError()
        if len(self._observations) < self.base_optimizer._initial_design._n_configs: # pylint: disable=protected-access
            raise RuntimeError('Surrogate model can make predictions *only* after all initial points have been evaluated')
        if self._space_adapter:
            configurations = self._space_adapter.inverse_transform(configurations)

        configs: npt.NDArray = convert_configurations_to_array(self._to_configspace_configs(configurations))
        mean_predictions, _ = self.base_optimizer._config_selector._model.predict(configs) # pylint: disable=protected-access
        return mean_predictions.reshape(-1,)

    def acquisition_function(self, configurations: pd.DataFrame, context: Optional[pd.DataFrame] = None) -> npt.NDArray:
        if context is not None:
            raise NotImplementedError()
        if self._space_adapter:
            configurations = self._space_adapter.inverse_transform(configurations)

        configs: list = self._to_configspace_configs(configurations)
        return self.base_optimizer._config_selector._acquisition_function(configs).reshape(-1,) # pylint: disable=protected-access

    def _to_configspace_configs(self, configurations: pd.DataFrame) -> list:
        """Convert a dataframe of configurations to a list of ConfigSpace configurations.

        Parameters
        ----------
        configurations : pd.DataFrame
            Dataframe of configurations / parameters. The columns are parameter names and the rows are the configurations.

        Returns
        -------
        configurations : list
            List of ConfigSpace configurations.
        """
        return [
            ConfigSpace.Configuration(self.optimizer_parameter_space, values=config.to_dict())
            for (_, config) in configurations.iterrows()
        ]

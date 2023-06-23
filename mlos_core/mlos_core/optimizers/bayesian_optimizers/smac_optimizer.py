#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Contains the wrapper class for SMAC Bayesian optimizers.
See Also: <https://automl.github.io/SMAC3/main/index.html>
"""

from pathlib import Path
from typing import Mapping, Optional
from tempfile import TemporaryDirectory

import ConfigSpace
import numpy.typing as npt
import pandas as pd

from mlos_core.optimizers.bayesian_optimizers.bayesian_optimizer import BaseBayesianOptimizer
from mlos_core.spaces.adapters.adapter import BaseSpaceAdapter


class SmacOptimizer(BaseBayesianOptimizer):
    """Wrapper class for SMAC based Bayesian optimization.

    Parameters
    ----------
    parameter_space : ConfigSpace.ConfigurationSpace
        The parameter space to optimize.

    space_adapter : BaseSpaceAdapter
        The space adapter class to employ for parameter space transformations.

    seed : Optional[int]
        By default SMAC uses a known seed (0) to keep results reproducible.
        However, if a `None` seed is explicitly provided, we let a random seed be produced by SMAC.

    run_name : Optional[str]
        Name of this run. This is used to easily distinguish across different runs.
        If set to `None` (default), SMAC will generate a hash from metadata.

    output_directory : Optional[str]
        The directory where SMAC output will saved. If set to `None` (default), a temporary dir will be used.

    max_trials : int
        Maximum number of trials (i.e., function evaluations) to be run. Defaults to 100.
        Note that modifying this value directly affects the value of `n_random_init`, if latter is set to `None`.

    n_random_init : Optional[int]
        Number of points evaluated at start to bootstrap the optimizer. Defaults to 10.

    n_random_probability: Optional[float]
        Probability of choosing to evaluate a random configuration during optimization.
        Defaults to `0.1`. Setting this to a higher value favors exploration over exploitation.
    """

    def __init__(self, *,  # pylint: disable=too-many-locals
                 parameter_space: ConfigSpace.ConfigurationSpace,
                 space_adapter: Optional[BaseSpaceAdapter] = None,
                 seed: Optional[int] = 0,
                 run_name: Optional[str] = None,
                 output_directory: Optional[str] = None,
                 max_trials: int = 100,
                 n_random_init: Optional[int] = 10,
                 n_random_probability: Optional[float] = 0.1):

        super().__init__(
            parameter_space=parameter_space,
            space_adapter=space_adapter,
        )

        # Declare at the top because we need it in __del__/cleanup()
        self._temp_output_directory: Optional[TemporaryDirectory] = None

        # pylint: disable=import-outside-toplevel
        from smac import HyperparameterOptimizationFacade as Optimizer_Smac
        from smac import Scenario
        from smac.intensifier.abstract_intensifier import AbstractIntensifier
        from smac.initial_design import LatinHypercubeInitialDesign
        from smac.main.config_selector import ConfigSelector
        from smac.random_design.probability_design import ProbabilityRandomDesign
        from smac.runhistory import TrialInfo

        # Store for TrialInfo instances returned by .ask()
        self.trial_info_map: Mapping[ConfigSpace.Configuration, TrialInfo] = {}

        # The default when not specified is to use a known seed (0) to keep results reproducible.
        # However, if a `None` seed is explicitly provided, we let a random seed be produced by SMAC.
        # https://automl.github.io/SMAC3/main/api/smac.scenario.html#smac.scenario.Scenario
        seed = -1 if seed is None else seed

        # Create temporary directory for SMAC output (if none provided)
        if output_directory is None:
            # pylint: disable=consider-using-with
            try:
                self._temp_output_directory = TemporaryDirectory(ignore_cleanup_errors=True)  # Argument added in Python 3.10
            except TypeError:
                self._temp_output_directory = TemporaryDirectory()
            output_directory = self._temp_output_directory.name

        scenario: Scenario = Scenario(
            self.optimizer_parameter_space,
            name=run_name,
            output_directory=Path(output_directory),
            deterministic=True,
            n_trials=max_trials,
            seed=seed or -1,  # if -1, SMAC will generate a random seed internally
            n_workers=1,  # Use a single thread for evaluating trials
        )
        intensifier: AbstractIntensifier = Optimizer_Smac.get_intensifier(scenario, max_config_calls=1)
        config_selector: ConfigSelector = ConfigSelector(scenario, retrain_after=1)

        initial_design: Optional[LatinHypercubeInitialDesign] = None
        if n_random_init is not None:
            initial_design = LatinHypercubeInitialDesign(scenario=scenario, n_configs=n_random_init)
        random_design: Optional[ProbabilityRandomDesign] = None
        if n_random_probability is not None:
            random_design = ProbabilityRandomDesign(probability=n_random_probability)

        self.base_optimizer = Optimizer_Smac(
            scenario,
            SmacOptimizer._dummy_target_func,
            initial_design=initial_design,
            intensifier=intensifier,
            random_design=random_design,
            config_selector=config_selector,
            overwrite=True,
        )

    def __del__(self) -> None:
        # Best-effort attempt to clean up, in case the user forgets to call .cleanup()
        self.cleanup()

    @staticmethod
    def _dummy_target_func(config: ConfigSpace.Configuration, seed: int = 0) -> None:
        """Dummy target function for SMAC optimizer.

        Since we only use the ask-and-tell interface, this is never called.

        Parameters
        ----------
        config : ConfigSpace.Configuration
            Configuration to evaluate.

        seed : int
            Random seed to use for the target function. Not actually used.
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
        from smac.runhistory import StatusType, TrialInfo, TrialValue  # pylint: disable=import-outside-toplevel

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
        from smac.runhistory import TrialInfo  # pylint: disable=import-outside-toplevel

        if context is not None:
            raise NotImplementedError()

        trial: TrialInfo = self.base_optimizer.ask()
        # Type ignore because this is WIP from ConfigSpace side
        # Check here: https://github.com/automl/ConfigSpace/issues/293
        self.trial_info_map[trial.config] = trial  # type: ignore
        return pd.DataFrame([trial.config], columns=self.optimizer_parameter_space.get_hyperparameter_names())

    def register_pending(self, configurations: pd.DataFrame, context: Optional[pd.DataFrame] = None) -> None:
        raise NotImplementedError()

    def surrogate_predict(self, configurations: pd.DataFrame, context: Optional[pd.DataFrame] = None) -> npt.NDArray:
        from smac.utils.configspace import convert_configurations_to_array  # pylint: disable=import-outside-toplevel

        if context is not None:
            raise NotImplementedError()
        if self._space_adapter:
            raise NotImplementedError()

        # pylint: disable=protected-access
        if len(self._observations) < self.base_optimizer._initial_design._n_configs:
            raise RuntimeError('Surrogate model can make predictions *only* after all initial points have been evaluated')
        if self.base_optimizer._config_selector._model is None:
            raise RuntimeError('Surrogate model is not yet trained')

        configs: npt.NDArray = convert_configurations_to_array(self._to_configspace_configs(configurations))
        mean_predictions, _ = self.base_optimizer._config_selector._model.predict(configs)
        return mean_predictions.reshape(-1,)

    def acquisition_function(self, configurations: pd.DataFrame, context: Optional[pd.DataFrame] = None) -> npt.NDArray:
        if context is not None:
            raise NotImplementedError()
        if self._space_adapter:
            raise NotImplementedError()

        # pylint: disable=protected-access
        if self.base_optimizer._config_selector._acquisition_function is None:
            raise RuntimeError('Acquisition function is not yet initialized')

        configs: list = self._to_configspace_configs(configurations)
        return self.base_optimizer._config_selector._acquisition_function(configs).reshape(-1,)

    def cleanup(self) -> None:
        if self._temp_output_directory is not None:
            self._temp_output_directory.cleanup()
            self._temp_output_directory = None

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

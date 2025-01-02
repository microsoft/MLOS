#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Contains the wrapper class for the :py:class:`.SmacOptimizer`.

Notes
-----
See the `SMAC3 Documentation <https://automl.github.io/SMAC3/main/index.html>`_ for
more details.
"""

from logging import warning
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING
from warnings import warn

import ConfigSpace
import numpy.typing as npt
import pandas as pd

from mlos_core.data_classes import Observation, Observations, Suggestion
from mlos_core.optimizers.bayesian_optimizers.bayesian_optimizer import (
    BaseBayesianOptimizer,
)
from mlos_core.spaces.adapters.adapter import BaseSpaceAdapter
from mlos_core.spaces.adapters.identity_adapter import IdentityAdapter


class SmacOptimizer(BaseBayesianOptimizer):
    """Wrapper class for SMAC based Bayesian optimization."""

    def __init__(
        self,
        *,  # pylint: disable=too-many-locals,too-many-arguments
        parameter_space: ConfigSpace.ConfigurationSpace,
        optimization_targets: list[str],
        objective_weights: list[float] | None = None,
        space_adapter: BaseSpaceAdapter | None = None,
        seed: int | None = 0,
        run_name: str | None = None,
        output_directory: str | None = None,
        max_trials: int = 100,
        n_random_init: int | None = None,
        max_ratio: float | None = None,
        use_default_config: bool = False,
        n_random_probability: float = 0.1,
    ):
        """
        Instantiate a new SMAC optimizer wrapper.

        Parameters
        ----------
        parameter_space : ConfigSpace.ConfigurationSpace
            The parameter space to optimize.

        optimization_targets : list[str]
            The names of the optimization targets to minimize.

        objective_weights : Optional[list[float]]
            Optional list of weights of optimization targets.

        space_adapter : BaseSpaceAdapter
            The space adapter class to employ for parameter space transformations.

        seed : int | None
            By default SMAC uses a known seed (0) to keep results reproducible.
            However, if a `None` seed is explicitly provided, we let a random seed
            be produced by SMAC.

        run_name : str | None
            Name of this run. This is used to easily distinguish across different runs.
            If set to `None` (default), SMAC will generate a hash from metadata.

        output_directory : str | None
            The directory where SMAC output will saved. If set to `None` (default),
            a temporary dir will be used.

        max_trials : int
            Maximum number of trials (i.e., function evaluations) to be run. Defaults to 100.
            Note that modifying this value directly affects the value of
            `n_random_init`, if latter is set to `None`.

        n_random_init : int | None
            Number of points evaluated at start to bootstrap the optimizer.
            Default depends on max_trials and number of parameters and max_ratio.
            Note: it can sometimes be useful to set this to 1 when pre-warming the
            optimizer from historical data. See Also:
            :py:meth:`mlos_bench.optimizers.base_optimizer.Optimizer.bulk_register`

        max_ratio : int | None
            Maximum ratio of max_trials to be random configs to be evaluated
            at start to bootstrap the optimizer.
            Useful if you want to explicitly control the number of random
            configs evaluated at start.

        use_default_config : bool
            Whether to use the default config for the first trial after random initialization.

        n_random_probability : float
            Probability of choosing to evaluate a random configuration during optimization.
            Defaults to `0.1`. Setting this to a higher value favors exploration over exploitation.
        """
        super().__init__(
            parameter_space=parameter_space,
            optimization_targets=optimization_targets,
            objective_weights=objective_weights,
            space_adapter=space_adapter,
        )

        # Declare at the top because we need it in __del__/cleanup()
        self._temp_output_directory: TemporaryDirectory | None = None

        # pylint: disable=import-outside-toplevel
        from smac import HyperparameterOptimizationFacade as Optimizer_Smac
        from smac import Scenario
        from smac.intensifier.abstract_intensifier import AbstractIntensifier
        from smac.main.config_selector import ConfigSelector
        from smac.random_design.probability_design import ProbabilityRandomDesign
        from smac.runhistory import TrialInfo
        from smac.utils.configspace import convert_configurations_to_array

        # Save util function here as a property for later usage, also to satisfy linter
        self._convert_configurations_to_array = convert_configurations_to_array

        # Store for TrialInfo instances returned by .ask()
        self.trial_info_map: dict[ConfigSpace.Configuration, TrialInfo] = {}

        # The default when not specified is to use a known seed (0) to keep results reproducible.
        # However, if a `None` seed is explicitly provided, we let a random seed be
        # produced by SMAC.
        # https://automl.github.io/SMAC3/main/api/smac.scenario.html#smac.scenario.Scenario
        seed = -1 if seed is None else seed

        # Create temporary directory for SMAC output (if none provided)
        if output_directory is None:
            # pylint: disable=consider-using-with
            try:
                # Argument added in Python 3.10
                self._temp_output_directory = TemporaryDirectory(ignore_cleanup_errors=True)
            except TypeError:
                self._temp_output_directory = TemporaryDirectory()
            output_directory = self._temp_output_directory.name
        assert output_directory is not None

        if n_random_init is not None:
            assert isinstance(n_random_init, int) and n_random_init >= 0
            if n_random_init == max_trials and use_default_config:
                # Increase max budgeted trials to account for use_default_config.
                max_trials += 1

        scenario: Scenario = Scenario(
            self.optimizer_parameter_space,
            objectives=self._optimization_targets,
            name=run_name,
            output_directory=Path(output_directory),
            deterministic=True,
            use_default_config=use_default_config,
            n_trials=max_trials,
            seed=seed or -1,  # if -1, SMAC will generate a random seed internally
            n_workers=1,  # Use a single thread for evaluating trials
        )
        intensifier: AbstractIntensifier = Optimizer_Smac.get_intensifier(
            scenario,
            max_config_calls=1,
        )
        config_selector: ConfigSelector = Optimizer_Smac.get_config_selector(
            scenario,
            retrain_after=1,
        )

        # TODO: When bulk registering prior configs to rewarm the optimizer,
        # there is a way to inform SMAC's initial design that we have
        # additional_configs and can set n_configs == 0.
        # Additionally, we may want to consider encoding those values into the
        # runhistory when prewarming the optimizer so that the initial design
        # doesn't reperform random init.
        # See Also: #488

        initial_design_args: dict[str, list | int | float | Scenario] = {
            "scenario": scenario,
            # Workaround a bug in SMAC that sets a default arg to a mutable
            # value that can cause issues when multiple optimizers are
            # instantiated with the use_default_config option within the same
            # process that use different ConfigSpaces so that the second
            # receives the default config from both as an additional config.
            "additional_configs": [],
        }
        if n_random_init is not None:
            initial_design_args["n_configs"] = n_random_init
            if n_random_init > 0.25 * max_trials and max_ratio is None:
                warning(
                    "Number of random initial configs (%d) is "
                    + "greater than 25%% of max_trials (%d). "
                    + "Consider setting max_ratio to avoid SMAC overriding n_random_init.",
                    n_random_init,
                    max_trials,
                )
            if max_ratio is not None:
                assert isinstance(max_ratio, float) and 0.0 <= max_ratio <= 1.0
                initial_design_args["max_ratio"] = max_ratio
            self._max_ratio = max_ratio

        # Use the default InitialDesign from SMAC.
        # (currently SBOL instead of LatinHypercube due to better uniformity
        # for initial sampling which results in lower overall samples required)
        initial_design = Optimizer_Smac.get_initial_design(
            **initial_design_args,  # type: ignore[arg-type]
        )
        # initial_design = LatinHypercubeInitialDesign(
        #    **initial_design_args,  # type: ignore[arg-type]
        # )

        # Workaround a bug in SMAC that doesn't pass the seed to the random
        # design when generated a random_design for itself via the
        # get_random_design static method when random_design is None.
        assert isinstance(n_random_probability, float) and n_random_probability >= 0
        random_design = ProbabilityRandomDesign(
            probability=n_random_probability,
            seed=scenario.seed,
        )

        self.base_optimizer = Optimizer_Smac(
            scenario,
            SmacOptimizer._dummy_target_func,
            initial_design=initial_design,
            intensifier=intensifier,
            random_design=random_design,
            config_selector=config_selector,
            multi_objective_algorithm=Optimizer_Smac.get_multi_objective_algorithm(
                scenario,
                objective_weights=self._objective_weights,
            ),
            overwrite=True,
            logging_level=False,  # Use the existing logger
        )

    def __del__(self) -> None:
        # Best-effort attempt to clean up, in case the user forgets to call .cleanup()
        self.cleanup()

    @property
    def max_ratio(self) -> float | None:
        """
        Gets the `max_ratio` parameter used in py:meth:`constructor <.__init__>` of this
        SmacOptimizer.

        Returns
        -------
        float
        """
        return self._max_ratio

    @property
    def n_random_init(self) -> int:
        """
        Gets the number of random samples to use to initialize the optimizer's search
        space sampling.

        Note: This may not be equal to the value passed to the initializer, due to
        logic present in the SMAC.

        See Also
        --------
        :py:attr:`.max_ratio`

        Returns
        -------
        int
            The number of random samples used to initialize the optimizer's search space sampling.
        """
        # pylint: disable=protected-access
        return self.base_optimizer._initial_design._n_configs

    @staticmethod
    def _dummy_target_func(config: ConfigSpace.Configuration, seed: int = 0) -> None:
        """
        Dummy target function for SMAC optimizer.

        Since we only use the ask-and-tell interface, this is never called.

        Parameters
        ----------
        config : ConfigSpace.Configuration
            Configuration to evaluate.

        seed : int
            Random seed to use for the target function. Not actually used.
        """
        # NOTE: Providing a target function when using the ask-and-tell interface is
        # an imperfection of the API -- this is planned to be fixed in some future
        # release: https://github.com/automl/SMAC3/issues/946
        raise RuntimeError("This function should never be called.")

    def _register(
        self,
        observations: Observations,
    ) -> None:
        """
        Registers one or more configs/score pairs (observations) with the underlying
        optimizer.

        Parameters
        ----------
        observations : Observations
            The set of config/scores to register.
        """
        # TODO: Implement bulk registration.
        # (e.g., by rebuilding the base optimizer instance with all observations).
        for observation in observations:
            self._register_single(observation)

    def _register_single(
        self,
        observation: Observation,
    ) -> None:
        """
        Registers the given config and its score.

        Parameters
        ----------
        observation: Observation
            The observation to register.
        """
        from smac.runhistory import (  # pylint: disable=import-outside-toplevel
            StatusType,
            TrialInfo,
            TrialValue,
        )

        if observation.context is not None:
            warn(
                f"Not Implemented: Ignoring context {list(observation.context.index)}",
                UserWarning,
            )

        # Retrieve previously generated TrialInfo (returned by .ask()) or create
        # new TrialInfo instance
        config = ConfigSpace.Configuration(
            self.optimizer_parameter_space,
            values=observation.config.dropna().to_dict(),
        )
        info: TrialInfo = self.trial_info_map.get(
            config,
            TrialInfo(config=config, seed=self.base_optimizer.scenario.seed),
        )
        value = TrialValue(
            cost=list(observation.score.astype(float)),
            time=0.0,
            status=StatusType.SUCCESS,
        )
        self.base_optimizer.tell(info, value, save=False)

        # Save optimizer once we register all configs
        self.base_optimizer.optimizer.save()

    def _suggest(
        self,
        *,
        context: pd.Series | None = None,
    ) -> Suggestion:
        """
        Suggests a new configuration.

        Parameters
        ----------
        context : pd.DataFrame
            Not Yet Implemented.

        Returns
        -------
        suggestion: Suggestion
            The suggestion to evaluate.
        """
        if TYPE_CHECKING:
            # pylint: disable=import-outside-toplevel,unused-import
            from smac.runhistory import TrialInfo

        if context is not None:
            warn(f"Not Implemented: Ignoring context {list(context.index)}", UserWarning)

        trial: TrialInfo = self.base_optimizer.ask()
        trial.config.check_valid_configuration()
        ConfigSpace.Configuration(
            self.optimizer_parameter_space,
            values=trial.config,
        ).check_valid_configuration()
        assert trial.config.config_space == self.optimizer_parameter_space
        self.trial_info_map[trial.config] = trial
        config_sr = pd.Series(dict(trial.config), dtype=object)
        return Suggestion(config=config_sr, context=context, metadata=None)

    def register_pending(self, pending: Suggestion) -> None:
        raise NotImplementedError()

    def surrogate_predict(self, suggestion: Suggestion) -> npt.NDArray:
        if suggestion.context is not None:
            warn(
                f"Not Implemented: Ignoring context {list(suggestion.context.index)}",
                UserWarning,
            )
        if self._space_adapter and not isinstance(self._space_adapter, IdentityAdapter):
            raise NotImplementedError("Space adapter not supported for surrogate_predict.")

        # pylint: disable=protected-access
        if len(self._observations) <= self.base_optimizer._initial_design._n_configs:
            raise RuntimeError(
                "Surrogate model can make predictions *only* after "
                "all initial points have been evaluated "
                f"{len(self._observations)} <= {self.base_optimizer._initial_design._n_configs}"
            )
        if self.base_optimizer._config_selector._model is None:
            raise RuntimeError("Surrogate model is not yet trained")

        config_array = self._convert_configurations_to_array(
            [
                ConfigSpace.Configuration(
                    self.optimizer_parameter_space, values=suggestion.config.to_dict()
                )
            ]
        )
        mean_predictions, _ = self.base_optimizer._config_selector._model.predict(config_array)
        return mean_predictions.reshape(
            -1,
        )

    def acquisition_function(self, suggestion: Suggestion) -> npt.NDArray:
        if suggestion.context is not None:
            warn(
                f"Not Implemented: Ignoring context {list(suggestion.context.index)}",
                UserWarning,
            )
        if self._space_adapter:
            raise NotImplementedError()

        # pylint: disable=protected-access
        if self.base_optimizer._config_selector._acquisition_function is None:
            raise RuntimeError("Acquisition function is not yet initialized")

        return self.base_optimizer._config_selector._acquisition_function(
            suggestion.config.config_to_configspace(self.optimizer_parameter_space)
        ).reshape(
            -1,
        )

    def cleanup(self) -> None:
        if hasattr(self, "_temp_output_directory") and self._temp_output_directory is not None:
            self._temp_output_directory.cleanup()
            self._temp_output_directory = None

    def _to_configspace_configs(self, *, configs: pd.DataFrame) -> list[ConfigSpace.Configuration]:
        """
        Convert a dataframe of configs to a list of ConfigSpace configs.

        Parameters
        ----------
        configs : pd.DataFrame
            Dataframe of configs / parameters. The columns are parameter names and
            the rows are the configs.

        Returns
        -------
        configs : list
            List of ConfigSpace configs.
        """
        return [
            ConfigSpace.Configuration(self.optimizer_parameter_space, values=config.to_dict())
            for (_, config) in configs.astype("O").iterrows()
        ]

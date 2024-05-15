#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Contains the wrapper class for SMAC Bayesian optimizers.
See Also: <https://automl.github.io/SMAC3/main/index.html>
"""

import inspect
import threading
from logging import warning
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union
from warnings import warn

import ConfigSpace
import numpy as np
import numpy.typing as npt
import pandas as pd
from mlos_core.optimizers.bayesian_optimizers.bayesian_optimizer import (
    BaseBayesianOptimizer,
)
from mlos_core.spaces.adapters.adapter import BaseSpaceAdapter
from mlos_core.spaces.adapters.identity_adapter import IdentityAdapter
from smac import HyperparameterOptimizationFacade as Optimizer_Smac
from smac import Scenario
from smac.facade import AbstractFacade
from smac.initial_design import AbstractInitialDesign, SobolInitialDesign
from smac.intensifier.abstract_intensifier import AbstractIntensifier
from smac.main.config_selector import ConfigSelector
from smac.random_design.probability_design import ProbabilityRandomDesign
from smac.runhistory import StatusType, TrialInfo, TrialValue


class SmacOptimizer(BaseBayesianOptimizer):
    """
    Wrapper class for SMAC based Bayesian optimization.
    """

    def __init__(
        self,  # pylint: disable=too-many-locals
        *,  # pylint: disable=too-many-locals
        parameter_space: ConfigSpace.ConfigurationSpace,
        space_adapter: Optional[BaseSpaceAdapter] = None,
        seed: Optional[int] = 0,
        run_name: Optional[str] = None,
        output_directory: Optional[str] = None,
        max_trials: int = 100,
        n_random_init: Optional[int] = None,
        max_ratio: Optional[float] = None,
        use_default_config: bool = False,
        n_random_probability: float = 0.1,
        facade: Type[AbstractFacade] = Optimizer_Smac,
        intensifier: Optional[Type[AbstractIntensifier]] = None,
        initial_design_class: Type[AbstractInitialDesign] = SobolInitialDesign,
        **kwargs: Any,
    ):
        """
        Instantiate a new SMAC optimizer wrapper.

        Parameters
        ----------
        parameter_space : ConfigSpace.ConfigurationSpace
            The parameter space to optimize.

        space_adapter : BaseSpaceAdapter
            The space adapter class to employ for parameter space
            transformations.

        seed : Optional[int]
            By default SMAC uses a known seed (0) to keep results reproducible.
            However, if a `None` seed is explicitly provided, we let a random
            seed be produced by SMAC.

        run_name : Optional[str]
            Name of this run. This is used to easily distinguish across
            different runs. If set to `None` (default), SMAC will generate a
            hash from metadata.

        output_directory : Optional[str]
            The directory where SMAC output will saved. If set to `None`
            (default), a temporary dir will be used.

        max_trials : int
            Maximum number of trials (i.e., function evaluations) to be run.
            Defaults to 100.
            Note that modifying this value directly affects the value of
            `n_random_init`, if latter is set to `None`.

        n_random_init : Optional[int]
            Number of points evaluated at start to bootstrap the optimizer.
            Default depends on max_trials and number of parameters and
            max_ratio.
            Note: it can sometimes be useful to set this to 1 when pre-warming
            the optimizer from historical data.
            See Also: mlos_bench.optimizer.bulk_register

        max_ratio : Optional[int]
            Maximum ratio of max_trials to be random configurations to be
            evaluated at start to bootstrap the optimizer.
            Useful if you want to explicitly control the number of random
            configurations evaluated at start.

        use_default_config: bool
            Whether to use the default config for the first trial after random
            initialization.

        n_random_probability: float
            Probability of choosing to evaluate a random configuration during
            optimization.
            Defaults to `0.1`. Setting this to a higher value favors
            exploration over exploitation.

        facade: AbstractFacade
            sets the facade to use for SMAC

        intensifier: Optional[Type[AbstractIntensifier]]
            Sets the intensifier type to use in the optimizer. If not set, the
            default intensifier
            from the facade will be used

        initial_design_class: AbstractInitialDesign
            Sets the initial design class to be used in the optimizer.
            Defaults to SobolInitialDesign

        **kwargs:
            Additional arguments to be passed to the
            scenerio, and intensifier
        """
        super().__init__(
            parameter_space=parameter_space,
            space_adapter=space_adapter,
        )

        # Declare at the top because we need it in __del__/cleanup()
        self._temp_output_directory: Optional[TemporaryDirectory] = None

        # Store for TrialInfo instances returned by .ask()
        self.trial_info_df: pd.DataFrame = pd.DataFrame(
            columns=["Configuration", "Context", "TrialInfo", "TrialValue"]
        )

        # The default when not specified is to use a known seed (0) to keep
        # results reproducible.
        # However, if a `None` seed is explicitly provided, we let a random
        # seed be produced by SMAC.
        # https://automl.github.io/SMAC3/main/api/smac.scenario.html#smac.scenario.Scenario
        seed = -1 if seed is None else seed

        # Create temporary directory for SMAC output (if none provided)
        if output_directory is None:
            # pylint: disable=consider-using-with
            try:
                self._temp_output_directory = TemporaryDirectory(
                    ignore_cleanup_errors=True
                )  # Argument added in Python 3.10
            except TypeError:
                self._temp_output_directory = TemporaryDirectory()
            output_directory = self._temp_output_directory.name

        if n_random_init is not None:
            assert isinstance(n_random_init, int) and n_random_init >= 0
            if n_random_init == max_trials and use_default_config:
                # Increase max budgeted trials to account for
                # use_default_config.
                max_trials += 1

        scenario: Scenario = Scenario(
            self.optimizer_parameter_space,
            name=run_name,
            output_directory=Path(output_directory),
            deterministic=True,
            use_default_config=use_default_config,
            n_trials=max_trials,
            seed=seed or -1,  # if -1, SMAC will generate a random seed
            n_workers=1,  # Use a single thread for evaluating trials
            **SmacOptimizer._filter_kwargs(Scenario, **kwargs),
        )

        config_selector: ConfigSelector = facade.get_config_selector(
            scenario, retrain_after=1
        )

        if intensifier is None:
            intensifier_instance = facade.get_intensifier(scenario)
        else:
            intensifier_instance = intensifier(
                scenario, **SmacOptimizer._filter_kwargs(intensifier, **kwargs)
            )

        # TODO: When bulk registering prior configs to rewarm the optimizer,
        # there is a way to inform SMAC's initial design that we have
        # additional_configs and can set n_configs == 0.
        # Additionally, we may want to consider encoding those values into the
        # runhistory when prewarming the optimizer so that the initial design
        # doesn't reperform random init.
        # See Also: #488

        initial_design_args: Dict[str, Union[list, int, float, Scenario]] = {
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
                    "Number of random initial configurations (%d) is "
                    + "greater than 25%% of max_trials (%d). "
                    + "Consider setting max_ratio to avoid SMAC overriding "
                    + "n_random_init.",
                    n_random_init,
                    max_trials,
                )
            if max_ratio is not None:
                assert isinstance(max_ratio, float) and 0.0 <= max_ratio <= 1.0
                initial_design_args["max_ratio"] = max_ratio

        # Use the default InitialDesign from SMAC.
        # (currently SOBOL instead of LatinHypercube due to better uniformity
        # for initial sampling which results in lower overall samples required)

        initial_design = initial_design_class(**initial_design_args)  # type: ignore

        # Workaround a bug in SMAC that doesn't pass the seed to the random
        # design when generated a random_design for itself via the
        # get_random_design static method when random_design is None.
        assert isinstance(n_random_probability, float) and n_random_probability >= 0
        random_design = ProbabilityRandomDesign(
            probability=n_random_probability, seed=scenario.seed
        )

        self.base_optimizer = facade(
            scenario,
            SmacOptimizer._dummy_target_func,
            initial_design=initial_design,
            intensifier=intensifier_instance,
            random_design=random_design,
            config_selector=config_selector,
            overwrite=True,
            logging_level=False,  # Use the existing logger
            **SmacOptimizer._filter_kwargs(facade, **kwargs),
        )

        self.lock = threading.Lock()

    def __del__(self) -> None:
        # Best-effort attempt to clean up, in case the user forgets to call .cleanup()
        self.cleanup()

    @property
    def n_random_init(self) -> int:
        """
        Gets the number of random samples to use to initialize the optimizer's search space sampling.

        Note: This may not be equal to the value passed to the initializer, due to logic present in the SMAC.
        See Also: max_ratio

        Returns
        -------
        int
            The number of random samples used to initialize the optimizer's search space sampling.
        """
        # pylint: disable=protected-access
        return self.base_optimizer._initial_design._n_configs

    @staticmethod
    def _filter_kwargs(function: Callable, **kwargs: Any) -> Dict[str, Any]:
        """
        Filters arguments provided in the kwargs dictionary to be restricted to the arugments legal for
        the called function.

        Parameters
        ----------
        function : Callable
            function over which we filter kwargs for.
        kwargs:
            kwargs that we are filtering for the target function

        Returns
        -------
        dict
            kwargs with the non-legal argument filtered out
        """
        sig = inspect.signature(function)
        filter_keys = [
            param.name
            for param in sig.parameters.values()
            if param.kind == param.POSITIONAL_OR_KEYWORD
        ]
        filtered_dict = {
            filter_key: kwargs[filter_key] for filter_key in filter_keys & kwargs.keys()
        }
        return filtered_dict

    @staticmethod
    def _dummy_target_func(
        config: ConfigSpace.Configuration,
        seed: int = 0,
        budget: float = 1,
        instance: object = None,
    ) -> None:
        """Dummy target function for SMAC optimizer.

        Since we only use the ask-and-tell interface, this is never called.

        Parameters
        ----------
        config : ConfigSpace.Configuration
            Configuration to evaluate.

        seed : int
            Random seed to use for the target function. Not actually used.

        budget : int
            The budget that was used for evaluating the configuration.

        instance : object
            The instance that the configuration was evaluated on.
        """
        # NOTE: Providing a target function when using the ask-and-tell interface is an imperfection of the API
        # -- this planned to be fixed in some future release: https://github.com/automl/SMAC3/issues/946
        raise RuntimeError("This function should never be called.")

    def _register(
        self,
        configurations: pd.DataFrame,
        scores: pd.Series,
        context: Optional[pd.DataFrame] = None,
    ) -> None:
        """Registers the given configurations and scores.

        Parameters
        ----------
        configurations : pd.DataFrame
            Dataframe of configurations / parameters. The columns are parameter names and the rows are the configurations.

        scores : pd.Series
            Scores from running the configurations. The index is the same as the index of the configurations.

        context : pd.DataFrame
            Context of the request that is being registered.
        """
        with self.lock:
            # Register each trial (one-by-one)
            contexts: List[pd.Series | None] = _to_context(context) or [
                None for _ in scores
            ]
            for config, score, ctx in zip(
                self._to_configspace_configs(configurations),
                scores.tolist(),
                contexts,
            ):
                value: TrialValue = TrialValue(
                    cost=score, time=0.0, status=StatusType.SUCCESS
                )

                # Retrieve previously generated TrialInfo (returned by .ask()) or create new TrialInfo instance
                if ctx is None:
                    matching: List = self.trial_info_df["Configuration"] == config
                else:
                    matching = (
                        self.trial_info_df["Configuration"] == config
                    ) & pd.Series(
                        [df_ctx.equals(ctx) for df_ctx in self.trial_info_df["Context"]]
                    )

                # make a new entry
                if sum(matching) > 0:
                    info = self.trial_info_df[matching]["TrialInfo"].iloc[-1]
                    self.trial_info_df.at[list(matching).index(True), "TrialValue"] = (
                        value
                    )
                else:
                    if ctx is None or "budget" not in ctx or "instance" not in ctx:
                        info = TrialInfo(
                            config=config, seed=self.base_optimizer.scenario.seed
                        )
                        self.trial_info_df.loc[len(self.trial_info_df.index)] = [
                            config,
                            info,
                            info,
                            value,
                        ]
                    else:
                        info = TrialInfo(
                            config=config,
                            seed=self.base_optimizer.scenario.seed,
                            budget=ctx["budget"],
                            instance=ctx["instance"],
                        )
                        self.trial_info_df.loc[len(self.trial_info_df.index)] = [
                            config,
                            ctx,
                            info,
                            value,
                        ]
                self.base_optimizer.tell(info, value, save=False)

            # Save optimizer once we register all configs
            self.base_optimizer.optimizer.save()

    def _suggest(
        self, context: Optional[pd.DataFrame] = None
    ) -> Tuple[pd.DataFrame, Optional[pd.DataFrame]]:
        """Suggests a new configuration.

        Parameters
        ----------
        context : pd.DataFrame
            Not Yet Implemented.

        Returns
        -------
        configuration : pd.DataFrame
            Pandas dataframe with a single row containing the configuration.
            Column names are the parameter names.

        context : pd.DataFrame
            Pandas dataframe with a single row containing the context.
            Column names are the budget, seed, and instance of the evaluation, if valid.
        """
        with self.lock:
            if context is not None:
                warn(
                    f"Not Implemented: Ignoring context {list(context.columns)}",
                    UserWarning,
                )

            trial: TrialInfo = self.base_optimizer.ask()
            trial.config.is_valid_configuration()
            self.optimizer_parameter_space.check_configuration(trial.config)
            assert trial.config.config_space == self.optimizer_parameter_space

            config_df = self._extract_config(trial)
            context_df = SmacOptimizer._extract_context(trial)

            self.trial_info_df.loc[len(self.trial_info_df.index)] = [
                trial.config,
                context_df.iloc[0],
                trial,
                None,
            ]

            return config_df, context_df

    def register_pending(
        self, configurations: pd.DataFrame, context: Optional[pd.DataFrame] = None
    ) -> None:
        raise NotImplementedError()

    def surrogate_predict(
        self, configurations: pd.DataFrame, context: Optional[pd.DataFrame] = None
    ) -> npt.NDArray:
        from smac.utils.configspace import (
            convert_configurations_to_array,  # pylint: disable=import-outside-toplevel
        )

        if context is not None:
            warn(
                f"Not Implemented: Ignoring context {list(context.columns)}",
                UserWarning,
            )
        if self._space_adapter and not isinstance(self._space_adapter, IdentityAdapter):
            raise NotImplementedError()

        # pylint: disable=protected-access
        if len(self._observations) <= self.base_optimizer._initial_design._n_configs:
            raise RuntimeError(
                "Surrogate model can make predictions *only* after all initial points have been evaluated "
                + f"{len(self._observations)} <= {self.base_optimizer._initial_design._n_configs}"
            )
        if self.base_optimizer._config_selector._model is None:
            raise RuntimeError("Surrogate model is not yet trained")

        configs: npt.NDArray = convert_configurations_to_array(
            self._to_configspace_configs(configurations)
        )
        mean_predictions, _ = self.base_optimizer._config_selector._model.predict(
            configs
        )
        return mean_predictions.reshape(
            -1,
        )

    def acquisition_function(
        self, configurations: pd.DataFrame, context: Optional[pd.DataFrame] = None
    ) -> npt.NDArray:
        if context is not None:
            warn(
                f"Not Implemented: Ignoring context {list(context.columns)}",
                UserWarning,
            )
        if self._space_adapter:
            raise NotImplementedError()

        # pylint: disable=protected-access
        if self.base_optimizer._config_selector._acquisition_function is None:
            raise RuntimeError("Acquisition function is not yet initialized")

        configs: list = self._to_configspace_configs(configurations)
        return self.base_optimizer._config_selector._acquisition_function(
            configs
        ).reshape(
            -1,
        )

    @staticmethod
    def _extract_context(trial: TrialInfo) -> pd.DataFrame:
        """Convert TrialInfo to a DataFrame.

        Parameters
        ----------
        trial : TrialInfo
            The trial to extract.

        Returns
        -------
        context : pd.DataFrame
            Pandas dataframe with a single row containing the context.
            Column names are the budget and instance of the evaluation, if valid.
        """
        return pd.DataFrame(
            [[trial.instance, trial.seed, trial.budget]],
            columns=["instance", "seed", "budget"],
        )

    def _extract_config(self, trial: TrialInfo) -> pd.DataFrame:
        return pd.DataFrame(
            [trial.config], columns=list(self.optimizer_parameter_space.keys())
        )

    def get_observations(self) -> pd.DataFrame:
        """Returns the observations as a dataframe.

        Returns
        -------
        observations : pd.DataFrame
            Dataframe of observations. The columns are parameter names and "score" for the score, each row is an observation.
        """
        if len(self._observations) == 0:
            raise ValueError("No observations registered yet.")
        configs = pd.concat([config for config, _, _ in self._observations])
        configs["score"] = pd.concat([score for _, score, _ in self._observations])

        return configs

    def get_observations_full(self) -> pd.DataFrame:
        """Returns the observations as a dataframe with additional info.

        Returns
        -------
        observations : pd.DataFrame
            Dataframe of observations. The columns are parameter names and "score" for the score, each row is an observation.
        """
        if len(self.trial_info_df) == 0:
            raise ValueError("No observations registered yet.")

        return self.trial_info_df

    def get_best_observation(self) -> pd.DataFrame:
        """Returns the best observation so far as a dataframe.

        Returns
        -------
        best_observation : pd.DataFrame
            Dataframe with a single row containing the best observation. The columns are parameter names and "score" for the score.
        """
        if len(self._observations) == 0:
            raise ValueError("No observations registered yet.")

        observations = self._observations

        max_budget = np.nan
        budgets = [
            context["budget"].max()
            for _, _, context in self._observations
            if context is not None
        ]
        if len(budgets) > 0:
            max_budget = max(budgets)

        if max_budget is not np.nan:
            observations = [
                (config, score, context)
                for config, score, context in self._observations
                if context is not None and context["budget"].max() == max_budget
            ]

        configs = pd.concat([config for config, _, _ in observations])
        scores = pd.concat([score for _, score, _ in observations])
        configs["score"] = scores

        return configs.nsmallest(1, columns="score")

    def cleanup(self) -> None:
        if self._temp_output_directory is not None:
            self._temp_output_directory.cleanup()
            self._temp_output_directory = None

    def _to_configspace_configs(
        self, configurations: pd.DataFrame
    ) -> List[ConfigSpace.Configuration]:
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
            ConfigSpace.Configuration(
                self.optimizer_parameter_space, values=config.to_dict()
            )
            for (_, config) in configurations.astype("O").iterrows()
        ]


def _to_context(contexts: Optional[pd.DataFrame]) -> Optional[List[pd.Series]]:
    if contexts is None:
        return None
    return [idx_series[1] for idx_series in contexts.iterrows()]

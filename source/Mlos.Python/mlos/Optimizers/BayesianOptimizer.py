#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import pandas as pd

from mlos.Logger import create_logger
from mlos.Optimizers.BayesianOptimizerConfigStore import bayesian_optimizer_config_store
from mlos.Optimizers.BayesianOptimizerConvergenceState import BayesianOptimizerConvergenceState
from mlos.Optimizers.OptimizerBase import OptimizerBase
from mlos.Optimizers.OptimizationProblem import OptimizationProblem
from mlos.Optimizers.ExperimentDesigner.ExperimentDesigner import ExperimentDesigner
from mlos.Optimizers.RegressionModels.GoodnessOfFitMetrics import DataSetType
from mlos.Optimizers.RegressionModels.HomogeneousRandomForestRegressionModel import HomogeneousRandomForestRegressionModel
from mlos.Tracer import trace
from mlos.Spaces import Point, SimpleHypergrid



class BayesianOptimizer(OptimizerBase):
    """Generic Bayesian Optimizer based on regresson model

    Uses extra trees as surrogate model and confidence bound acquisition function by default.

    Attributes
    ----------
    logger : Logger
    optimization_problem : OptimizationProblem
    surrogate_model : HomogeneousRandomForestRegressionModel
    optimizer_config : Point
    experiment_designer: ExperimentDesigner

    """
    @trace()
    def __init__(
            self,
            optimization_problem: OptimizationProblem,
            optimizer_config: Point,
            logger=None
    ):
        if logger is None:
            logger = create_logger("BayesianOptimizer")
        self.logger = logger

        # Let's initialize the optimizer.
        #
        assert len(optimization_problem.objectives) == 1, "For now this is a single-objective optimizer."
        OptimizerBase.__init__(self, optimization_problem)

        # Since the optimization_problem.objective_space can now be multi-dimensional (as a milestone towards multi-objective
        # optimization), we have to prepare a smaller objective space for the surrogate model.
        # TODO: create multiple models each predicting a different objective. Also consider multi-objective models.
        #
        assert not optimization_problem.objective_space.is_hierarchical(), "Not supported."
        only_objective = optimization_problem.objectives[0]
        self.surrogate_model_output_space = SimpleHypergrid(
            name="surrogate_model_output_space",
            dimensions=[optimization_problem.objective_space[only_objective.name]]
        )

        assert optimizer_config in bayesian_optimizer_config_store.parameter_space, "Invalid config."
        self.optimizer_config = optimizer_config

        # Now let's put together the surrogate model.
        #
        assert self.optimizer_config.surrogate_model_implementation == HomogeneousRandomForestRegressionModel.__name__, "TODO: implement more"
        self.surrogate_model = HomogeneousRandomForestRegressionModel(
            model_config=self.optimizer_config.homogeneous_random_forest_regression_model_config,
            input_space=self.optimization_problem.feature_space,
            output_space=self.surrogate_model_output_space,
            logger=self.logger
        )

        # Now let's put together the experiment designer that will suggest parameters for each experiment.
        #
        assert self.optimizer_config.experiment_designer_implementation == ExperimentDesigner.__name__
        self.experiment_designer = ExperimentDesigner(
            designer_config=self.optimizer_config.experiment_designer_config,
            optimization_problem=self.optimization_problem,
            surrogate_model=self.surrogate_model,
            logger=self.logger
        )

        self._optimizer_convergence_state = BayesianOptimizerConvergenceState(
            surrogate_model_fit_state=self.surrogate_model.fit_state
        )

        # Also let's make sure we have the dataframes we need for the surrogate model.
        #
        self._parameter_names = [dimension.name for dimension in self.optimization_problem.parameter_space.dimensions]
        self._parameter_names_set = set(self._parameter_names)

        self._context_names = ([dimension.name for dimension in self.optimization_problem.context_space.dimensions]
                               if self.optimization_problem.context_space else [])
        self._context_names_set = set(self._context_names)

        self._target_names = [dimension.name for dimension in self.optimization_problem.objective_space.dimensions]
        self._target_names_set = set(self._target_names)

        self._parameter_values_df = pd.DataFrame(columns=self._parameter_names)
        self._context_values_df = pd.DataFrame(columns=self._context_names)
        self._target_values_df = pd.DataFrame(columns=self._target_names)

    @property
    def trained(self):
        return self.surrogate_model.trained

    @property
    def num_observed_samples(self):
        return len(self._parameter_values_df.index)

    def compute_surrogate_model_goodness_of_fit(self):
        if not self.surrogate_model.trained:
            raise RuntimeError("Model has not been trained yet.")
        feature_values_pandas_frame = self.optimization_problem.construct_feature_dataframe(parameter_values=self._parameter_values_df.copy(),
                                                                                            context_values=self._context_values_df.copy())
        return self.surrogate_model.compute_goodness_of_fit(
            features_df=feature_values_pandas_frame,
            target_df=self._target_values_df.copy(),
            data_set_type=DataSetType.TRAIN
        )

    def get_optimizer_convergence_state(self):
        return self._optimizer_convergence_state

    def get_all_observations(self):
        return self._parameter_values_df.copy(), self._target_values_df.copy(), self._context_values_df.copy()

    @trace()
    def suggest(self, random=False, context: Point = None):
        if self.optimization_problem.context_space is not None:
            if context is None:
                raise ValueError("Context required by optimization problem but not provided.")
            assert context in self.optimization_problem.context_space
        random = random or self.num_observed_samples < self.optimizer_config.min_samples_required_for_guided_design_of_experiments
        context_values = context.to_dataframe() if context is not None else None
        suggested_config = self.experiment_designer.suggest(random=random, context_values_dataframe=context_values)
        assert suggested_config in self.optimization_problem.parameter_space
        return suggested_config

    @trace()
    def register(self, parameter_values_pandas_frame, target_values_pandas_frame, context_values_pandas_frame=None):
        # TODO: add to a Dataset and move on. The surrogate model should have a reference to the same dataset
        # TODO: and should be able to refit automatically.

        if self.optimization_problem.context_space is not None and context_values_pandas_frame is None:
            raise ValueError("Context required by optimization problem but not provided.")

        parameter_columns_to_retain = [column for column in parameter_values_pandas_frame.columns if column in self._parameter_names_set]
        target_columns_to_retain = [column for column in target_values_pandas_frame.columns if column in self._target_names_set]

        if len(parameter_columns_to_retain) == 0:
            raise ValueError(f"None of the {parameter_values_pandas_frame.columns} is a parameter recognized by this optimizer.")

        if len(target_columns_to_retain) == 0:
            raise ValueError(f"None of {target_values_pandas_frame.columns} is a target recognized by this optimizer.")

        parameter_values_pandas_frame = parameter_values_pandas_frame[parameter_columns_to_retain]
        target_values_pandas_frame = target_values_pandas_frame[target_columns_to_retain]

        all_null_parameters = parameter_values_pandas_frame[parameter_values_pandas_frame.isnull().all(axis=1)]
        if len(all_null_parameters.index) > 0:
            raise ValueError(f"{len(all_null_parameters.index)} of the observations contain(s) no valid parameters.")

        all_null_context = parameter_values_pandas_frame[parameter_values_pandas_frame.isnull().all(axis=1)]
        if len(all_null_context.index) > 0:
            raise ValueError(f"{len(all_null_context.index)} of the observations contain(s) no valid context.")

        all_null_targets = target_values_pandas_frame[target_values_pandas_frame.isnull().all(axis=1)]
        if len(all_null_targets.index) > 0:
            raise ValueError(f"{len(all_null_targets.index)} of the observations contain(s) no valid targets")

        if context_values_pandas_frame is not None:
            if len(parameter_values_pandas_frame) != len(context_values_pandas_frame):
                raise ValueError(f"Incompatible shape of parameters and context: "
                                 f"{parameter_values_pandas_frame.shape} and {context_values_pandas_frame.shape}.")
            context_columns_to_retain = [column for column in context_values_pandas_frame.columns if column in self._context_names_set]
            if len(context_columns_to_retain) == 0:
                raise ValueError(f"None of the {context_values_pandas_frame.columns} is a context recognized by this optimizer.")
            context_values_pandas_frame = context_values_pandas_frame[context_columns_to_retain]
            self._context_values_df = self._context_values_df.append(context_values_pandas_frame, ignore_index=True)

        self._parameter_values_df = self._parameter_values_df.append(parameter_values_pandas_frame, ignore_index=True)
        self._target_values_df = self._target_values_df.append(target_values_pandas_frame, ignore_index=True)

        # TODO: ascertain that min_samples_required ... is more than min_samples to fit the model
        if self.num_observed_samples >= self.optimizer_config.min_samples_required_for_guided_design_of_experiments:
            feature_values_pandas_frame = self.optimization_problem.construct_feature_dataframe(
                parameter_values=self._parameter_values_df, context_values=self._context_values_df)
            self.surrogate_model.fit(
                feature_values_pandas_frame=feature_values_pandas_frame,
                target_values_pandas_frame=self._target_values_df,
                iteration_number=len(self._parameter_values_df.index)
            )

    @trace()
    def predict(self, parameter_values_pandas_frame, t=None, context_values_pandas_frame=None):  # pylint: disable=unused-argument
        # TODO: make this streaming and/or using arrow.
        #
        feature_values_pandas_frame = self.optimization_problem.construct_feature_dataframe(parameter_values=parameter_values_pandas_frame,
                                                                                            context_values=context_values_pandas_frame)
        return self.surrogate_model.predict(feature_values_pandas_frame)

    def focus(self, subspace):
        ...

    def reset_focus(self):
        ...

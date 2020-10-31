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
from mlos.Optimizers.RegressionModels.GoodnessOfFitMetrics import DataSetType, GoodnessOfFitMetrics
from mlos.Optimizers.RegressionModels.HomogeneousRandomForestRegressionModel import HomogeneousRandomForestRegressionModel
from mlos.Tracer import trace
from mlos.Spaces import Point



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

        assert optimizer_config in bayesian_optimizer_config_store.parameter_space, "Invalid config."
        self.optimizer_config = optimizer_config

        # Now let's put together the surrogate model.
        #
        assert self.optimizer_config.surrogate_model_implementation == HomogeneousRandomForestRegressionModel.__name__, "TODO: implement more"
        self.surrogate_model = HomogeneousRandomForestRegressionModel(
            model_config=self.optimizer_config.homogeneous_random_forest_regression_model_config,
            input_space=self.optimization_problem.parameter_space, # TODO: change to feature space
            output_space=self.optimization_problem.objective_space,
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
        # TODO: this will need a better home - either a DataSet class or the surrogate model itself.
        self._feature_values_df = pd.DataFrame(columns=[dimension.name for dimension in self.optimization_problem.parameter_space.dimensions])
        self._target_values_df = pd.DataFrame(columns=[dimension.name for dimension in self.optimization_problem.objective_space.dimensions])

    @property
    def trained(self):
        return self.surrogate_model.trained

    @property
    def num_observed_samples(self):
        return len(self._feature_values_df.index)

    def compute_surrogate_model_goodness_of_fit(self):
        if not self.surrogate_model.trained:
            raise RuntimeError("Model has not been trained yet.")
        return self.surrogate_model.compute_goodness_of_fit(features_df=self._feature_values_df.copy(), target_df=self._target_values_df.copy(), data_set_type=DataSetType.TRAIN)

    def get_optimizer_convergence_state(self):
        return self._optimizer_convergence_state

    def get_all_observations(self):
        return self._feature_values_df.copy(), self._target_values_df.copy()

    @trace()
    def suggest(self, random=False, context=None):
        # TODO: pass context to the suggest method
        random = random or self.num_observed_samples < self.optimizer_config.min_samples_required_for_guided_design_of_experiments
        suggested_config = self.experiment_designer.suggest(random=random)
        assert suggested_config in self.optimization_problem.parameter_space
        return suggested_config

    @trace()
    def register(self, feature_values_pandas_frame, target_values_pandas_frame):
        # TODO: add to a Dataset and move on. The surrogate model should have a reference to the same dataset
        # TODO: and should be able to refit automatically.

        self._feature_values_df = self._feature_values_df.append(feature_values_pandas_frame, ignore_index=True)
        self._target_values_df = self._target_values_df.append(target_values_pandas_frame, ignore_index=True)

        # TODO: ascertain that min_samples_required ... is more than min_samples to fit the model
        if self.num_observed_samples >= self.optimizer_config.min_samples_required_for_guided_design_of_experiments:
            self.surrogate_model.fit(
                feature_values_pandas_frame=self._feature_values_df,
                target_values_pandas_frame=self._target_values_df,
                iteration_number=len(self._feature_values_df.index)
            )

    @trace()
    def predict(self, feature_values_pandas_frame, t=None):
        return self.surrogate_model.predict(feature_values_pandas_frame)

    def focus(self, subspace):
        ...

    def reset_focus(self):
        ...

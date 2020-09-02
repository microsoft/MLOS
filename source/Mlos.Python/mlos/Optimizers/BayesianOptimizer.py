#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import pandas as pd

from mlos.Logger import create_logger
from mlos.Tracer import trace
from mlos.Spaces import CategoricalDimension, DiscreteDimension, Point, SimpleHypergrid, DefaultConfigMeta

from mlos.Optimizers.BayesianOptimizerConvergenceState import BayesianOptimizerConvergenceState
from mlos.Optimizers.OptimizerInterface import OptimizerInterface
from mlos.Optimizers.OptimizationProblem import OptimizationProblem
from mlos.Optimizers.ExperimentDesigner.ExperimentDesigner import ExperimentDesigner, ExperimentDesignerConfig
from mlos.Optimizers.RegressionModels.GoodnessOfFitMetrics import DataSetType
from mlos.Optimizers.RegressionModels.HomogeneousRandomForestRegressionModel import HomogeneousRandomForestRegressionModel,\
    HomogeneousRandomForestRegressionModelConfig


class BayesianOptimizerConfig(metaclass=DefaultConfigMeta):

    CONFIG_SPACE = SimpleHypergrid(
        name="bayesian_optimizer_config",
        dimensions=[
            CategoricalDimension(name="surrogate_model_implementation", values=[HomogeneousRandomForestRegressionModel.__name__]),
            CategoricalDimension(name="experiment_designer_implementation", values=[ExperimentDesigner.__name__]),
            DiscreteDimension(name="min_samples_required_for_guided_design_of_experiments", min=2, max=10000)
        ]
    ).join(
        subgrid=HomogeneousRandomForestRegressionModelConfig.CONFIG_SPACE,
        on_external_dimension=CategoricalDimension(name="surrogate_model_implementation", values=[HomogeneousRandomForestRegressionModel.__name__])
    ).join(
        subgrid=ExperimentDesignerConfig.CONFIG_SPACE,
        on_external_dimension=CategoricalDimension(name="experiment_designer_implementation", values=[ExperimentDesigner.__name__])
    )

    _DEFAULT = Point(
        surrogate_model_implementation=HomogeneousRandomForestRegressionModel.__name__,
        experiment_designer_implementation=ExperimentDesigner.__name__,
        min_samples_required_for_guided_design_of_experiments=10,
        homogeneous_random_forest_regression_model_config=HomogeneousRandomForestRegressionModelConfig.DEFAULT,
        experiment_designer_config=ExperimentDesignerConfig.DEFAULT
    )


class BayesianOptimizer(OptimizerInterface):
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
        OptimizerInterface.__init__(self, optimization_problem)

        assert optimizer_config in BayesianOptimizerConfig.CONFIG_SPACE, "Invalid config."
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
    def num_observed_samples(self):
        return len(self._feature_values_df.index)

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
            self.surrogate_model.compute_goodness_of_fit(features_df=self._feature_values_df, target_df=self._target_values_df, data_set_type=DataSetType.TRAIN)

    @trace()
    def predict(self, feature_values_pandas_frame, t=None):
        return self.surrogate_model.predict(feature_values_pandas_frame)

    @trace()
    def optimum(self, stay_focused=False):
        if self.optimization_problem.objectives[0].minimize:
            index_of_best_target = self._target_values_df.idxmin()[0]
        else:
            index_of_best_target = self._target_values_df.idxmax()[0]
        objective_name = self.optimization_problem.objectives[0].name
        best_objective_value = self._target_values_df.loc[index_of_best_target][objective_name]

        param_names = [dimension.name for dimension in self.optimization_problem.parameter_space.dimensions]
        params_for_best_objective = self._feature_values_df.loc[index_of_best_target]

        optimal_config_and_target = {
            objective_name: best_objective_value,
        }

        for param_name in param_names:
            optimal_config_and_target[param_name] = params_for_best_objective[param_name]

        return optimal_config_and_target

    def focus(self, subspace):
        ...

    def reset_focus(self):
        ...

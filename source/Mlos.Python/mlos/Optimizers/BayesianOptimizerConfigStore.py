#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from mlos.Spaces import SimpleHypergrid, DiscreteDimension, CategoricalDimension, Point
from mlos.Spaces.Configs.ComponentConfigStore import ComponentConfigStore

from mlos.Optimizers.ExperimentDesigner.ExperimentDesigner import ExperimentDesigner, ExperimentDesignerConfig
from mlos.Optimizers.RegressionModels.HomogeneousRandomForestConfigStore import HomogeneousRandomForestConfigStore
from mlos.Optimizers.RegressionModels.HomogeneousRandomForestRegressionModel import HomogeneousRandomForestRegressionModel


BayesianOptimizerConfigStore = ComponentConfigStore(
    parameter_space=SimpleHypergrid(
        name="bayesian_optimizer_config",
        dimensions=[
            CategoricalDimension(name="surrogate_model_implementation", values=[
                HomogeneousRandomForestRegressionModel.__name__,
            ]),
            CategoricalDimension(name="experiment_designer_implementation", values=[ExperimentDesigner.__name__]),
            DiscreteDimension(name="min_samples_required_for_guided_design_of_experiments", min=2, max=10000)
        ]
    ).join(
        subgrid=HomogeneousRandomForestConfigStore.parameter_space,
        on_external_dimension=CategoricalDimension(name="surrogate_model_implementation", values=[HomogeneousRandomForestRegressionModel.__name__])
    ).join(
        subgrid=ExperimentDesignerConfig.CONFIG_SPACE,
        on_external_dimension=CategoricalDimension(name="experiment_designer_implementation", values=[ExperimentDesigner.__name__])
    ),
    default=Point(
        surrogate_model_implementation=HomogeneousRandomForestRegressionModel.__name__,
        experiment_designer_implementation=ExperimentDesigner.__name__,
        min_samples_required_for_guided_design_of_experiments=10,
        homogeneous_random_forest_regression_model_config=HomogeneousRandomForestConfigStore.default,
        experiment_designer_config=ExperimentDesignerConfig.DEFAULT
    ),
    description="TODO"
)

# Add a config with homogeneous random forest where the decision trees refit for every new observation.
#
optimizer_config = BayesianOptimizerConfigStore.default
optimizer_config.homogeneous_random_forest_regression_model_config.decision_tree_regression_model_config.n_new_samples_before_refit = 1
optimizer_config.homogeneous_random_forest_regression_model_config.n_estimators = 50
BayesianOptimizerConfigStore.add_config_by_name(
    config_name='default_refit_tree_every_time',
    config_point=optimizer_config
)

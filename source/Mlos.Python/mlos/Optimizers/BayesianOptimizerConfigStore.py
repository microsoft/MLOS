#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from mlos.Spaces import SimpleHypergrid, DiscreteDimension, CategoricalDimension, Point
from mlos.Spaces.Configs.ComponentConfigStore import ComponentConfigStore

from mlos.Optimizers.ExperimentDesigner.ExperimentDesigner import ExperimentDesigner, experiment_designer_config_store
from mlos.Optimizers.RegressionModels.HomogeneousRandomForestConfigStore import homogeneous_random_forest_config_store
from mlos.Optimizers.RegressionModels.HomogeneousRandomForestRegressionModel import HomogeneousRandomForestRegressionModel
from mlos.Optimizers.RegressionModels.MultiObjectiveHomogeneousRandomForest import MultiObjectiveHomogeneousRandomForest


bayesian_optimizer_config_store = ComponentConfigStore(
    parameter_space=SimpleHypergrid(
        name="bayesian_optimizer_config",
        dimensions=[
            CategoricalDimension(name="surrogate_model_implementation", values=[
                HomogeneousRandomForestRegressionModel.__name__,
                MultiObjectiveHomogeneousRandomForest.__name__
            ]),
            CategoricalDimension(name="experiment_designer_implementation", values=[ExperimentDesigner.__name__]),
            DiscreteDimension(name="min_samples_required_for_guided_design_of_experiments", min=2, max=100)
        ]
    ).join(
        subgrid=homogeneous_random_forest_config_store.parameter_space,
        on_external_dimension=CategoricalDimension(
            name="surrogate_model_implementation",
            values=[
                HomogeneousRandomForestRegressionModel.__name__,
                MultiObjectiveHomogeneousRandomForest.__name__
            ])
    ).join(
        subgrid=experiment_designer_config_store.parameter_space,
        on_external_dimension=CategoricalDimension(name="experiment_designer_implementation", values=[ExperimentDesigner.__name__])
    ),
    default=Point(
        surrogate_model_implementation=HomogeneousRandomForestRegressionModel.__name__,
        experiment_designer_implementation=ExperimentDesigner.__name__,
        min_samples_required_for_guided_design_of_experiments=10,
        homogeneous_random_forest_regression_model_config=homogeneous_random_forest_config_store.default,
        experiment_designer_config=experiment_designer_config_store.default
    ),
    description="TODO"
)

# Add a config with homogeneous random forest where the decision trees refit for every new observation.
#
optimizer_config = bayesian_optimizer_config_store.default
optimizer_config.homogeneous_random_forest_regression_model_config.decision_tree_regression_model_config.n_new_samples_before_refit = 1
optimizer_config.homogeneous_random_forest_regression_model_config.n_estimators = 50
bayesian_optimizer_config_store.add_config_by_name(
    config_name='default_refit_tree_every_time',
    config_point=optimizer_config
)

# Add a default config with glowworm swarm optimizer
#
bayesian_optimizer_config_store.add_config_by_name(
    config_name="default_with_glow_worm",
    config_point=Point(
        surrogate_model_implementation=HomogeneousRandomForestRegressionModel.__name__,
        experiment_designer_implementation=ExperimentDesigner.__name__,
        min_samples_required_for_guided_design_of_experiments=10,
        homogeneous_random_forest_regression_model_config=homogeneous_random_forest_config_store.default,
        experiment_designer_config=experiment_designer_config_store.get_config_by_name("default_glow_worm_config")
    )
)

bayesian_optimizer_config_store.add_config_by_name(
    config_name="default_with_random_near_incumbent_config",
    config_point=Point(
        surrogate_model_implementation=HomogeneousRandomForestRegressionModel.__name__,
        experiment_designer_implementation=ExperimentDesigner.__name__,
        min_samples_required_for_guided_design_of_experiments=10,
        homogeneous_random_forest_regression_model_config=homogeneous_random_forest_config_store.default,
        experiment_designer_config=experiment_designer_config_store.get_config_by_name("default_random_near_incumbent_config")
    )
)

# A default multi-objective optimizer config.
#
default_multi_objective_optimizer_config = Point(
    surrogate_model_implementation=MultiObjectiveHomogeneousRandomForest.__name__,
    experiment_designer_implementation=ExperimentDesigner.__name__,
    min_samples_required_for_guided_design_of_experiments=10,
    homogeneous_random_forest_regression_model_config=homogeneous_random_forest_config_store.default,
    experiment_designer_config=experiment_designer_config_store.get_config_by_name("default_multi_objective_config")
)

bayesian_optimizer_config_store.add_config_by_name(
    config_name="default_multi_objective_optimizer_config",
    config_point=default_multi_objective_optimizer_config
)

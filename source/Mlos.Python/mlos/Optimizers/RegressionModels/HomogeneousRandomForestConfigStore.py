#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from mlos.Optimizers.RegressionModels.DecisionTreeRegressionModel import DecisionTreeRegressionModel, decision_tree_config_store
from mlos.Spaces import SimpleHypergrid, ContinuousDimension, DiscreteDimension, CategoricalDimension, Point
from mlos.Spaces.Configs.ComponentConfigStore import ComponentConfigStore

homogeneous_random_forest_config_store = ComponentConfigStore(
    parameter_space=SimpleHypergrid(
        name="homogeneous_random_forest_regression_model_config",
        dimensions=[
            DiscreteDimension(name="n_estimators", min=1, max=256),
            ContinuousDimension(name="features_fraction_per_estimator", min=0, max=1, include_min=False, include_max=True),
            ContinuousDimension(name="samples_fraction_per_estimator", min=0.2, max=1, include_min=False, include_max=True),
            CategoricalDimension(name="regressor_implementation", values=[DecisionTreeRegressionModel.__name__]),
            CategoricalDimension(name="bootstrap", values=[True, False])
        ]
    ).join(
        subgrid=decision_tree_config_store.parameter_space,
        on_external_dimension=CategoricalDimension(name="regressor_implementation", values=[DecisionTreeRegressionModel.__name__])
    ),
    default=Point(
        n_estimators=10,
        features_fraction_per_estimator=1,
        samples_fraction_per_estimator=0.7,
        regressor_implementation=DecisionTreeRegressionModel.__name__,
        decision_tree_regression_model_config=decision_tree_config_store.default,
        bootstrap=True
    ),
    description="TODO"
)

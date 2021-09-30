#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from mlos.Optimizers.RegressionModels.LassoCrossValidatedRegressionModel import LassoCrossValidatedRegressionModel, lasso_cross_validated_config_store
from mlos.Optimizers.RegressionModels.SklearnRandomForestRegressionModelConfig import SklearnRandomForestRegressionModelConfig
from mlos.Spaces import SimpleHypergrid, DiscreteDimension, CategoricalDimension, Point
from mlos.Spaces.Configs.ComponentConfigStore import ComponentConfigStore

# TODO : Add back the RidgeRegressionModel boosting_root_model option after adding new RidgeCrossValidatedRegressionModel
# TODO : Move from Sklearn random forest to HomogeneousRandomForest

regression_enhanced_random_forest_config_store = ComponentConfigStore(
    parameter_space=SimpleHypergrid(
        name="regression_enhanced_random_forest_regression_model_config",
        dimensions=[
            DiscreteDimension(name="max_basis_function_degree", min=1, max=10),
            CategoricalDimension(name="residual_model_name",
                                 values=[SklearnRandomForestRegressionModelConfig.__name__]),
            CategoricalDimension(name="boosting_root_model_name",
                                 values=[LassoCrossValidatedRegressionModel.__name__]),
            CategoricalDimension(name="perform_initial_random_forest_hyper_parameter_search",
                                 values=[True, False])
        ]
    ).join(
        subgrid=lasso_cross_validated_config_store.parameter_space,
        on_external_dimension=CategoricalDimension(name="boosting_root_model_name",
                                                   values=[LassoCrossValidatedRegressionModel.__name__])
    ).join(
        subgrid=SklearnRandomForestRegressionModelConfig.CONFIG_SPACE,
        on_external_dimension=CategoricalDimension(name="residual_model_name",
                                                   values=[SklearnRandomForestRegressionModelConfig.__name__])
    ),
    default=Point(
        max_basis_function_degree=2,
        residual_model_name=SklearnRandomForestRegressionModelConfig.__name__,
        boosting_root_model_name=LassoCrossValidatedRegressionModel.__name__,
        lasso_regression_model_config=lasso_cross_validated_config_store.default,
        sklearn_random_forest_regression_model_config=SklearnRandomForestRegressionModelConfig.DEFAULT,
        perform_initial_random_forest_hyper_parameter_search=False
    ),
    description="Regression-enhanced random forest model hyper-parameters. "
                "Model inspired by : https://arxiv.org/pdf/1904.10416.pdf"
)

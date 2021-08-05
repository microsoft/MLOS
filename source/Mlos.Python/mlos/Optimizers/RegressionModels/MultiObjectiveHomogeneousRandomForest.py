#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from mlos.Optimizers.RegressionModels.HomogeneousRandomForestRegressionModel import HomogeneousRandomForestRegressionModel
from mlos.Optimizers.RegressionModels.HomogeneousRandomForestConfigStore import homogeneous_random_forest_config_store
from mlos.Optimizers.RegressionModels.NaiveMultiObjectiveRegressionModel import NaiveMultiObjectiveRegressionModel
from mlos.Spaces import Hypergrid, Point, SimpleHypergrid


class MultiObjectiveHomogeneousRandomForest(NaiveMultiObjectiveRegressionModel):
    """Maintains multiple HomogeneousRandomForestRegressionModels each predicting a different objective.

    All single-objective models are configured according to model_config.

    """
    def __init__(
            self,
            model_config: Point,
            input_space: Hypergrid,
            output_space: Hypergrid,
            logger=None
    ):
        NaiveMultiObjectiveRegressionModel.__init__(
            self,
            model_type=HomogeneousRandomForestRegressionModel,
            model_config=model_config,
            input_space=input_space,
            output_space=output_space,
            logger=logger
        )


        # We just need to assert that the model config belongs in homogeneous_random_forest_config_store.parameter_space.
        # A more elaborate solution might be needed down the road, but for now this simple solution should suffice.
        #
        assert model_config in homogeneous_random_forest_config_store.parameter_space

        for output_dimension in output_space.dimensions:
            random_forest = HomogeneousRandomForestRegressionModel(
                model_config=model_config,
                input_space=input_space,
                output_space=SimpleHypergrid(name=f"{output_dimension.name}_objective", dimensions=[output_dimension]),
                logger=self.logger
            )
            self._regressors_by_objective_name[output_dimension.name] = random_forest

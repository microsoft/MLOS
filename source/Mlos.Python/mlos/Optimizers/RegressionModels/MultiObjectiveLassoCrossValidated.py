#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import logging
from mlos.Optimizers.RegressionModels.LassoCrossValidatedConfigStore import lasso_cross_validated_config_store
from mlos.Optimizers.RegressionModels.LassoCrossValidatedRegressionModel import LassoCrossValidatedRegressionModel
from mlos.Optimizers.RegressionModels.NaiveMultiObjectiveRegressionModel import NaiveMultiObjectiveRegressionModel
from mlos.Spaces import Hypergrid, Point, SimpleHypergrid


class MultiObjectiveLassoCrossValidated(NaiveMultiObjectiveRegressionModel):
    """Maintains multiple LassoCrossValidatedRegressionModels each predicting a different objective.

    All single-objective models are configured according to model_config.

    """
    def __init__(
            self,
            model_config: Point,
            input_space: Hypergrid,
            output_space: Hypergrid,
            logger: logging.Logger = None
    ):
        NaiveMultiObjectiveRegressionModel.__init__(
            self,
            model_type=LassoCrossValidatedRegressionModel,
            model_config=model_config,
            input_space=input_space,
            output_space=output_space,
            logger=logger
        )


        # We just need to assert that the model config belongs in lasso_cross_validated_config_store.parameter_space.
        # A more elaborate solution might be needed down the road, but for now this simple solution should suffice.
        #
        assert model_config in lasso_cross_validated_config_store.parameter_space

        for output_dimension in output_space.dimensions:
            print(f'output_dimension.name: {output_dimension.name}')
            lasso_model = LassoCrossValidatedRegressionModel(
                model_config=model_config,
                input_space=input_space,
                output_space=SimpleHypergrid(name=f"{output_dimension.name}_objective", dimensions=[output_dimension]),
                logger=self.logger
            )
            self._regressors_by_objective_name[output_dimension.name] = lasso_model

#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import logging
from mlos.Optimizers.RegressionModels.RegressionEnhancedRandomForestConfigStore import regression_enhanced_random_forest_config_store
from mlos.Optimizers.RegressionModels.RegressionEnhancedRandomForestModel import RegressionEnhancedRandomForestRegressionModel
from mlos.Optimizers.RegressionModels.NaiveMultiObjectiveRegressionModel import NaiveMultiObjectiveRegressionModel
from mlos.Spaces import Hypergrid, Point, SimpleHypergrid


class MultiObjectiveRegressionEnhancedRandomForest(NaiveMultiObjectiveRegressionModel):
    """Maintains multiple RegressionEnhancedRandomForestRegressionModel each predicting a different objective.

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
            model_type=RegressionEnhancedRandomForestRegressionModel,
            model_config=model_config,
            input_space=input_space,
            output_space=output_space,
            logger=logger
        )


        # We just need to assert that the model config belongs in regression_enhanced_random_forest_config_store.parameter_space.
        # A more elaborate solution might be needed down the road, but for now this simple solution should suffice.
        #
        assert model_config in regression_enhanced_random_forest_config_store.parameter_space

        for output_dimension in output_space.dimensions:
            # We copy the model_config (rather than share across objectives below because the perform_initial_random_forest_hyper_parameter_search
            #  is set to False after the initial fit() call so that subsequent .fit() calls don't pay the cost penalty for this embedded hyper parameter search
            rerf_model = RegressionEnhancedRandomForestRegressionModel(
                model_config=model_config.copy(),
                input_space=input_space,
                output_space=SimpleHypergrid(name=f"{output_dimension.name}_objective", dimensions=[output_dimension]),
                logger=self.logger
            )
            self._regressors_by_objective_name[output_dimension.name] = rerf_model

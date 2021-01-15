#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import numpy as np
import pandas as pd
from scipy.stats import t
from mlos.Logger import create_logger
from mlos.Optimizers.ExperimentDesigner.UtilityFunctions.UtilityFunction import UtilityFunction
from mlos.Optimizers.ParetoFrontier import ParetoFrontier
from mlos.Optimizers.RegressionModels.MultiObjectiveRegressionModel import MultiObjectiveRegressionModel
from mlos.Optimizers.RegressionModels.Prediction import Prediction
from mlos.Optimizers.RegressionModels.MultiObjectivePrediction import MultiObjectivePrediction
from mlos.Spaces import SimpleHypergrid, ContinuousDimension, CategoricalDimension, DiscreteDimension, Point
from mlos.Spaces.Configs.ComponentConfigStore import ComponentConfigStore
from mlos.Tracer import trace
from mlos.Utils.KeyOrderedDict import KeyOrderedDict


multi_objective_probability_of_improvement_utility_function_config_store = ComponentConfigStore(
    parameter_space=SimpleHypergrid(
        name="multi_objective_probability_of_improvement",
        dimensions=[
            CategoricalDimension(name="utility_function_name", values=["multi_objective_probability_of_improvement"]),
            DiscreteDimension(name="num_monte_carlo_samples", min=100, max=100000)
        ]
    ),
    default=Point(
        utility_function_name="upper_confidence_bound_on_improvement",
        alpha=0.01
    )
)



class MultiObjectiveProbabilityOfImprovementUtilityFunction(UtilityFunction):
    """Computes the probability of improvement (POI) of a set of configurations over the existing pareto frontier.

    We are up against several requirements here: we need to be able to predict the probability of improvement in a multi-dimensional
    objective space. Our assumptions (see below) make each distribution a multi-dimensional blob that's cut in two by a nearly
    arbitrarily complex surface of the pareto frontier. This precludes any closed form solution to the POI question.

    Thus, we take a Monte Carlo approach: we generate a bunch of points from the predictive distribution, compute the proportion of
    these that are dominated by the existing pareto frontier, and use that proportion as an estimator for the probability of
    improvement.

    Assuming Prediction Error Independence:

        We assume that we can sample independently from the distributions described by the multi-objective prediction object. That
        is to say that if we assume:

            P(objective_2 = y2 | objective_1 = y1) == P(objective_2 = y2)

        In practice I do not know how often this assumption is true. On the one hand, correlations between objective_1 and
        objective_2 should have been picked up by the model doing the predictions so by the time we get here, assuming that prediction
        errors are uncorrelated seems at least partly defensible. On the other hand, if for example predictions came from leaves at
        the edge of the parameter space then the predictions can effectively be extrapolations. In such a case, the prediction errors
        are correlated and our Monte Carlo sampling is biased.

        I don't know how important this is in practice so I propose going forward with this simple solution, and treating it as
        as a baseline that more sophisticated approaches can improve upon in the future.

    """
    def __init__(
        self,
        function_config: Point,
        surrogate_model: MultiObjectiveRegressionModel,
        logger=None
    ):
        if logger is None:
            logger = create_logger(self.__class__.__name__)
        self.logger = logger

        self.config = function_config
        if self.config.utility_function_name not in ("multi_objective_probability_of_improvement"):
            raise RuntimeError(f"Invalid utility function name: {self.config.utility_function_name}.")

        self.surrogate_model: MultiObjectiveRegressionModel = surrogate_model


    @trace()
    def __call__(
        self,
        feature_values_pandas_frame: pd.DataFrame,
        pareto_df: pd.DataFrame
    ):
        self.logger.debug(f"Computing utility values for {len(feature_values_pandas_frame.index)} points.")

        feature_values_pandas_frame = self.surrogate_model.input_space.filter_out_invalid_rows(feature_values_pandas_frame)
        multi_objective_predictions: MultiObjectivePrediction = self.surrogate_model.predict(features_df=feature_values_pandas_frame)


        # Now that we have predictions for all of the features_df rows, we need to sample random points from the distribution
        # described by each prediction and then we want to check how many of those random points are dominated by the existing
        # pareto frontier. The proportion of non-dominated to all points is our estimator for the probability of improvement.
        # Note that we could compute the confidence intervals on the POI, and we could in theory keep sampling more intelligently.
        # That is, we could reject really dominated configurations after only a few samples, but if there are any close contenders,
        # we could sample more aggressively from their distributions until we reach a statistically significant difference between
        # their POI esitmates (and then sample a bit more, to fortify our conclusions).

        predicted_value_col = Prediction.LegalColumnNames.PREDICTED_VALUE.value
        dof_col = Prediction.LegalColumnNames.PREDICTED_VALUE_DEGREES_OF_FREEDOM.value

        poi_df = pd.DataFrame(index=feature_values_pandas_frame.index, columns='utility')

        # Let's make sure all predictions have a standard deviation available.
        #
        for _, objective_prediction in multi_objective_predictions:
            std_dev_column_name = objective_prediction.add_standard_deviation_column()

        for config_idx in feature_values_pandas_frame.index:
            monte_carlo_samples_df = pd.DataFrame()

            for objective_name, prediction in multi_objective_predictions:
                prediction_df = prediction.get_dataframe()
                config_prediction = prediction_df.loc[config_idx]
                monte_carlo_samples_df[objective_name] = np.random.standard_t(config_prediction[dof_col], self.config.num_monte_carlo_samples) \
                                             * config_prediction[std_dev_column_name] \
                                             + config_prediction[predicted_value_col]

            # At this point we have a dataframe with all the randomly generated points in the objective space. Let's query the pareto
            # frontier if they are dominated or not
            num_dominated_points = ParetoFrontier.is_dominated(objectives_df=monte_carlo_samples_df, pareto_df=pareto_df).sum()
            probability_of_improvement = num_dominated_points / self.config.num_monte_carlo_samples
            poi_df.loc[config_idx, 'utility'] = probability_of_improvement

        return poi_df

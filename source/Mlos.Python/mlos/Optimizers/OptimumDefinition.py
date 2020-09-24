#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from enum import Enum

class OptimumDefinition(Enum):
    """Enumerates all supported definitions of optimum.

    The optimum can be defined in a number of ways. For single objective optimization these include:
        1. Best observation.
        2. Tested configuration with the highest:
            1. predicted value (different from observed values in the presence of noise and when the model doesn't fit traininig data perfectly)
            2. upper confidence bound on predicted value
            3. lower confidence bound on predicted value
        3. Speculative optima - kick off the utility function optimizer to find configurations with:
            1. maximum predicted value
            2. maximum upper confidence bound on predicted value
            3. maximum lower confidence bound on predicted value.

    For multi-objective optimization this will be a Pareto Frontier build out of any of the above.

        We want the user to be able to specify which of the above definitions is of interest to them. The hypothesis is that this definition should match
    the utility function, but we will have to see the data to be sure.

    """

    # Good choice for objective functions with little or no noise.
    #
    BEST_OBSERVATION = 'best_observation'

    # The center of the prediction interval for an observed configuration. Treacherous if the prediction interval is wide.
    #
    PREDICTED_VALUE_FOR_OBSERVED_CONFIG = 'predicted_value_for_observed_config'

    # Configuration with the maximum upper confidence bound on predicted value. For maximization problems this is the risk seeking optimum especially
    # if the prediction intervals are wide. For minimization problems this is a risk averting, or regret minimizing definition of optimum.
    #
    UPPER_CONFIDENCE_BOUND_FOR_OBSERVED_CONFIG = 'prediction_upper_confidence_bound_for_observed_config'

    # Similar to UPPER_CONFIDENCE_BOUND_FOR_OBSERVED_CONFIG except the risk profiles are swapped. For maximization problems this is a risk averting
    # definition of optimum, whereas for minimization problems this is a risk seeking approach.
    #
    LOWER_CONFIDENCE_BOUND_FOR_OBSERVED_CONFIG = 'prediction_lower_confidence_bound_for_observed_config'

    # These three definitions will be similar to the values above, except they are speculative. They could potentially return a configuration that
    # has not been observed. Exercise caution.
    #
    # SPECULATIVE_BEST_PREDICTED_VALUE = 'speculative_best_predicted_value'
    # SPECULATIVE_BEST_UPPER_CONFIDENCE_BOUND = 'speculative_best_upper_confidence_bound'
    # SPECULATIVE_BEST_LOWER_CONFIDENCE_BOUND = 'speculative_best_lower_confidence_bound'

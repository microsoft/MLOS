#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from enum import Enum

from mlos.Spaces import SimpleHypergrid, ContinuousDimension, DiscreteDimension, CategoricalDimension, Point
from mlos.Spaces.Configs.ComponentConfigStore import ComponentConfigStore

class Criterion(Enum):
    """ The function to measure the quality of a split.

    Supported criteria are 'mse' for the mean squared error, which is equal to variance reduction as feature
    selection criterion and minimizes the L2 loss using the mean of each terminal node, 'friedman_mse',
    which uses mean squared error with Friedman’s improvement score for potential splits, and 'mae' for the
    mean absolute error, which minimizes the L1 loss using the median of each terminal node.
    """
    MSE = 'mse'
    FRIEDMAN_MSE = 'friedman_mse'
    MAE = 'mae'

class Splitter(Enum):
    """ The strategy used to choose the split at each node.

    Supported strategies are “best” to choose the best split and “random” to choose the best random split.
    """
    BEST = "best"
    RANDOM = "random"

class MaxFeaturesFunc(Enum):
    AUTO = "auto"
    SQRT = "sqrt"
    LOG2 = "log2"

decision_tree_config_store = ComponentConfigStore(
    parameter_space=SimpleHypergrid(
        name="decision_tree_regression_model_config",
        dimensions=[
            CategoricalDimension(name="criterion", values=[criterion.value for criterion in Criterion]),
            CategoricalDimension(name="splitter", values=[splitter.value for splitter in Splitter]),
            DiscreteDimension(name="max_depth", min=0, max=2**10),
            DiscreteDimension(name="min_samples_split", min=2, max=2**10),
            DiscreteDimension(name="min_samples_leaf", min=3, max=2**10),
            ContinuousDimension(name="min_weight_fraction_leaf", min=0.0, max=0.5),
            CategoricalDimension(name="max_features", values=[function.value for function in MaxFeaturesFunc]),
            DiscreteDimension(name="max_leaf_nodes", min=0, max=2**10),
            ContinuousDimension(name="min_impurity_decrease", min=0.0, max=2**10),
            ContinuousDimension(name="ccp_alpha", min=0.0, max=2**10),
            DiscreteDimension(name="min_samples_to_fit", min=1, max=2 ** 32),
            DiscreteDimension(name="n_new_samples_before_refit", min=1, max=2**32)
        ]
    ),
    default=Point(
        criterion=Criterion.MSE.value,
        splitter=Splitter.BEST.value,
        max_depth=0,
        min_samples_split=2,
        min_samples_leaf=3,
        min_weight_fraction_leaf=0.0,
        max_features=MaxFeaturesFunc.AUTO.value,
        max_leaf_nodes=0,
        min_impurity_decrease=0.0,
        ccp_alpha=0.0,
        min_samples_to_fit=10,
        n_new_samples_before_refit=10
    ),
    description="Governs the construction of an instance of a decision tree regressor. Most of the parameters are passed directly"
                "to the DecisionTreeRegressor constructor. Two exceptions: "
                "min_samples_to_fit determines the minimum number of samples required for the tree to be fitted."
                "n_new_samples_before_refit determines the number of new samples before a tree will be refitted."
                "Copied from scikit-learn docs:"
                "criterion: The function to measure the quality of a split."
                "splitter: The strategy used to choose the split at each node."
                "max_depth: The maximum depth of the tree. If None, then nodes are expanded until all leaves are pure or until all leaves contain less than"
                " min_samples_split samples."
                "min_samples_split: The minimum number of samples required to split an internal node."
                "min_samples_leaf: The minimum number of samples required to be at a leaf node."
                "min_weight_fraction_leaf: The minimum weighted fraction of the sum total of weights (of all the input samples) required to be at a leaf node."
                " Samples have equal weight when sample_weight is not provided."
                "max_features: The number of features to consider when looking for the best split."
                "random_state: If int, random_state is the seed used by the random number generator; If RandomState instance, random_state is the random number"
                " generator; If None, the random number generator is the RandomState instance used by np.random."
                "max_leaf_nodes: Grow a tree with max_leaf_nodes in best-first fashion. Best nodes are defined as relative reduction in impurity. If None then"
                " unlimited number of leaf nodes."
                "min_impurity_decrease: A node will be split if this split induces a decrease of the impurity greater than or equal to this value."
                "ccp_alpha: complexity parameter used for Minimal Cost-Complexity Pruning. The subtree with the largest cost complexity that is smaller than"
                " ccp_alpha will be chosen. By default, no pruning is performed. See Minimal Cost-Complexity Pruning for details."
                "min_samples_to_fit: minimum number of samples before it makes sense to try to fit this tree"
                "n_new_samples_before_refit: It makes little sense to refit every model for every sample. This parameter controls"
                " how frequently we refit the decision tree."
)

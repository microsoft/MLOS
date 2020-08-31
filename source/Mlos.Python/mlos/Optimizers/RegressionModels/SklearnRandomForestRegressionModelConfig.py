#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from enum import Enum

from mlos.Spaces import SimpleHypergrid, \
    ContinuousDimension, DiscreteDimension, CategoricalDimension, Point

from .RegressionModel import RegressionModelConfig

class SklearnRandomForestRegressionModelConfig(RegressionModelConfig):
    class MaxFeatures(Enum):
        """
        The number of features to consider when looking for the best split
            - If "auto", then `max_features=n_features`.
            - If "sqrt", then `max_features=sqrt(n_features)`.
            - If "log2", then `max_features=log2(n_features)`.
            - If None, then `max_features=n_features`.
        """
        AUTO = "auto"
        SQRT = "sqrt"
        LOG2 = "log2"

    class Criterion(Enum):
        """
        The function to measure the quality of a split. Supported criteria
            are "mse" for the mean squared error, which is equal to variance
            reduction as feature selection criterion, and "mae" for the mean
            absolute error.
        """
        MSE = "mse"
        MAE = "mae"

    CONFIG_SPACE = SimpleHypergrid(
        name="sklearn_random_forest_regression_model_config",
        dimensions=[
            DiscreteDimension(name="n_estimators", min=1, max=2 ** 10),
            CategoricalDimension(name="criterion", values=[criterion.value for criterion in Criterion]),
            DiscreteDimension(name="max_depth", min=0, max=2 ** 10),
            ContinuousDimension(name="min_samples_split", min=2, max=2 ** 10),
            ContinuousDimension(name="min_samples_leaf", min=1, max=2 ** 10),
            ContinuousDimension(name="min_weight_fraction_leaf", min=0, max=0.5),
            CategoricalDimension(name="max_features", values=[max_feature.value for max_feature in MaxFeatures]),
            DiscreteDimension(name="max_leaf_nodes", min=0, max=2 ** 10),
            ContinuousDimension(name="min_impurity_decrease", min=0, max=2 ** 10),
            CategoricalDimension(name="bootstrap", values=[False, True]),
            CategoricalDimension(name="oob_score", values=[False, True]),
            DiscreteDimension(name="n_jobs", min=1, max=2 ** 10),
            CategoricalDimension(name="warm_start", values=[False, True]),
            ContinuousDimension(name="ccp_alpha", min=0, max=2 ** 10),
            ContinuousDimension(name="max_samples", min=0, max=2 ** 10)
        ]
    )

    _DEFAULT = Point(
        n_estimators=100,
        criterion=Criterion.MSE.value,
        max_depth=0,  # overloading 0 as None to deal with sklearn param type interpretation
        min_samples_split=2,
        min_samples_leaf=1,
        min_weight_fraction_leaf=0.0,
        max_features=MaxFeatures.AUTO.value,
        max_leaf_nodes=0,  # overloading 0 as None to deal with sklearn param type interpretation
        min_impurity_decrease=0,
        bootstrap=True,
        oob_score=False,
        n_jobs=1,
        warm_start=False,
        ccp_alpha=0,
        max_samples=0
    )

    @classmethod
    def contains(cls, config):
        return Point(
            n_estimators=config.n_estimators,
            criterion=config.criterion,
            max_depth=config.max_depth,
            min_samples_split=config.min_samples_split,
            min_samples_leaf=config.min_samples_leaf,
            min_weight_fraction_leaf=config.min_weight_fraction_leaf,
            max_features=config.max_features,
            max_leaf_nodes=config.max_leaf_nodes,
            min_impurity_decrease=config.min_impurity_decrease,
            bootstrap=config.bootstrap,
            oob_score=config.oob_score,
            n_jobs=config.n_jobs,
            warm_start=config.warm_start,
            ccp_alpha=config.ccp_alpha,
            max_samples=config.max_samples
        ) in cls.CONFIG_SPACE

    @classmethod
    def create_from_config_point(cls, config_point):
        assert cls.contains(config_point)
        config_key_value_pairs = {param_name: value for param_name, value in config_point}
        return cls(**config_key_value_pairs)

    def __init__(
            self,
            n_estimators=_DEFAULT.n_estimators,
            criterion=_DEFAULT.criterion,
            max_depth=_DEFAULT.max_depth,
            min_samples_split=_DEFAULT.min_samples_split,
            min_samples_leaf=_DEFAULT.min_samples_leaf,
            min_weight_fraction_leaf=_DEFAULT.min_weight_fraction_leaf,
            max_features=_DEFAULT.max_features,
            max_leaf_nodes=_DEFAULT.max_leaf_nodes,
            min_impurity_decrease=_DEFAULT.min_impurity_decrease,
            bootstrap=_DEFAULT.bootstrap,
            oob_score=_DEFAULT.oob_score,
            n_jobs=_DEFAULT.n_jobs,
            warm_start=_DEFAULT.warm_start,
            ccp_alpha=_DEFAULT.ccp_alpha,
            max_samples=_DEFAULT.max_samples
    ):
        """
        Random Forest parameters:
        :param n_estimators: The number of trees in the forest.
        :param criterion: The function to measure the quality of a split. Supported criteria
            are "mse" for the mean squared error, which is equal to variance
            reduction as feature selection criterion, and "mae" for the mean
            absolute error.
        :param max_depth: The maximum depth of the tree. If None, then nodes are expanded until
            all leaves are pure or until all leaves contain less than min_samples_split samples.
        :param min_samples_split: The minimum number of samples required to split an internal node
        :param min_samples_leaf: The minimum number of samples required to be at a leaf node.
            A split point at any depth will only be considered if it leaves at
            least ``min_samples_leaf`` training samples in each of the left and
            right branches.  This may have the effect of smoothing the model,
            especially in regression.
        :param min_weight_fraction_leaf: The minimum weighted fraction of the sum total of weights (of all
            the input samples) required to be at a leaf node.
        :param max_features: The number of features to consider when looking for the best split
            - If "auto", then `max_features=n_features`.
            - If "sqrt", then `max_features=sqrt(n_features)`.
            - If "log2", then `max_features=log2(n_features)`.
            - If None, then `max_features=n_features`.
        :param max_leaf_nodes: Grow trees with ``max_leaf_nodes`` in best-first fashion.
        :param min_impurity_decrease: A node will be split if this split induces a decrease of the impurity
            greater than or equal to this value.
        :param bootstrap: Whether bootstrap samples are used when building trees. If False, the
            whole dataset is used to build each tree.
        :param oob_score: Whether to use out-of-bag samples to estimate the R^2 on unseen data.
        :param n_jobs: The number of jobs to run in parallel. :meth:`fit`, :meth:`predict`,
            :meth:`decision_path` and :meth:`apply` are all parallelized over the
            trees.
        :param warm_start: When set to ``True``, reuse the solution of the previous call to fit
            and add more estimators to the ensemble, otherwise, just fit a whole
            new forest.
        :param ccp_alpha: Complexity parameter used for Minimal Cost-Complexity Pruning. The
            subtree with the largest cost complexity that is smaller than
            ``ccp_alpha`` will be chosen.
            .. versionadded:: 0.22
        :param max_samples: If bootstrap is True, the number of samples to draw from X
            to train each base estimator.
        """
        self.n_estimators = n_estimators
        self.criterion = criterion
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.min_samples_leaf = min_samples_leaf
        self.min_weight_fraction_leaf = min_weight_fraction_leaf
        self.max_features = max_features
        self.max_leaf_nodes = max_leaf_nodes
        self.min_impurity_decrease = min_impurity_decrease
        self.bootstrap = bootstrap
        self.oob_score = oob_score
        self.n_jobs = n_jobs
        self.warm_start = warm_start
        self.ccp_alpha = ccp_alpha
        self.max_samples = max_samples

    # sklearn random forest regressor interprets max_depth = None differently than an int value
    #  so mapping max_depth=0 to None here
    @property
    def max_depth_value(self):
        if self.max_depth == 0:
            return None
        return self.max_depth

    @property
    # similar mapping here as for max_depth
    def max_leaf_nodes_value(self):
        if self.max_leaf_nodes == 0 or self.max_leaf_nodes == 1:
            return None
        return self.max_leaf_nodes

    @property
    # similar mapping here as for max_depth
    def max_sample_value(self):
        if self.max_samples == 0:
            return None
        return self.max_samples

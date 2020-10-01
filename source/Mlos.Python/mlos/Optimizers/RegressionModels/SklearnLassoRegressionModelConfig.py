#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from enum import Enum

from mlos.Spaces import SimpleHypergrid, \
    ContinuousDimension, DiscreteDimension, CategoricalDimension, Point

from .RegressionModel import RegressionModelConfig


class SklearnLassoRegressionModelConfig(RegressionModelConfig):
    class Selection(Enum):
        """
        Parameter to sklearn lasso regressor controlling how model coefficients are selected for update.
        From  https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.Lasso.html:
        If set to ‘random’, a random coefficient is updated every iteration rather than looping
        over features sequentially by default. This (setting to ‘random’) often leads to significantly
        faster convergence especially when tol is higher than 1e-4.
        """
        CYCLIC = 'cyclic'
        RANDOM = 'random'

    CONFIG_SPACE = SimpleHypergrid(
        name="sklearn_lasso_regression_model_config",
        dimensions=[
            ContinuousDimension(name="alpha", min=0, max=2 ** 16),
            CategoricalDimension(name="fit_intercept", values=[False, True]),
            CategoricalDimension(name="normalize", values=[False, True]),
            CategoricalDimension(name="precompute", values=[False, True]),
            CategoricalDimension(name="copy_x", values=[False, True]),
            DiscreteDimension(name="max_iter", min=0, max=10 ** 5),
            ContinuousDimension(name="tol", min=0, max=2 ** 10),
            CategoricalDimension(name="warm_start", values=[False, True]),
            CategoricalDimension(name="positive", values=[False, True]),
            CategoricalDimension(name="selection", values=[selection.value for selection in Selection]),
        ]
    )
    _DEFAULT = Point(
        selection=Selection.CYCLIC.value,
        alpha=1.0,
        fit_intercept=True,
        normalize=False,
        # sklearn model expects precompute type str, bool, array-like, so setting to default and exclude list option
        precompute=False,
        copy_x=True,
        max_iter=1000,
        tol=10 ** -4,
        warm_start=False,
        positive=False
    )

    @classmethod
    def contains(cls, config):
        return Point(
            alpha=config.alpha,
            fit_intercept=config.fit_intercept,
            normalize=config.normalize,
            precompute=config.precompute,
            copy_x=config.copy_x,
            max_iter=config.max_iter,
            tol=config.tol,
            warm_start=config.warm_start,
            positive=config.positive,
            selection=config.selection
        ) in cls.CONFIG_SPACE

    @classmethod
    def create_from_config_point(cls, config_point):
        assert cls.contains(config_point)
        config_key_value_pairs = {param_name: value for param_name, value in config_point}
        return cls(**config_key_value_pairs)

    def __init__(
            self,
            alpha=_DEFAULT.alpha,
            fit_intercept=_DEFAULT.fit_intercept,
            normalize=_DEFAULT.normalize,
            precompute=_DEFAULT.precompute,
            copy_x=_DEFAULT.copy_x,
            max_iter=_DEFAULT.max_iter,
            tol=_DEFAULT.tol,
            warm_start=_DEFAULT.warm_start,
            positive=_DEFAULT.positive,
            random_state=None,
            selection=_DEFAULT.selection
    ):
        """
        Lasso parameters:
        :param alpha: Constant that multiplies the L1 term. Defaults to 1.0.
        :param fit_intercept: Whether to calculate the intercept for this model.
        :param normalize: This parameter is ignored when ``fit_intercept`` is set to False.
            If True, the regressors X will be normalized before regression by
            subtracting the mean and dividing by the l2-norm.
        :param precompute: Whether to use a precomputed Gram matrix to speed up
            calculations. If set to ``'auto'`` let us decide.
        :param copy_x: If ``True``, X will be copied; else, it may be overwritten.
        :param max_iter: The maximum number of iterations
        :param tol: The tolerance for the optimization: if the updates are
            smaller than ``tol``, the optimization code checks the
            dual gap for optimality and continues until it is smaller
            than ``tol``.
        :param warm_start: When set to True, reuse the solution of the previous call to fit as
            initialization, otherwise, just erase the previous solution.
        :param positive: When set to ``True``, forces the coefficients to be positive.
        :param random_state: The seed of the pseudo random number generator that selects a random
            feature to update. Used when ``selection`` == 'random'.
        :param selection: {'cyclic', 'random'} If set to 'random', a random coefficient is updated every iteration
            rather than looping over features sequentially by default.
        """
        self.alpha = alpha
        self.fit_intercept = fit_intercept
        self.normalize = normalize
        self.precompute = precompute
        self.copy_x = copy_x
        self.max_iter = max_iter
        self.tol = tol
        self.warm_start = warm_start
        self.positive = positive
        self.random_state = random_state
        self.selection = selection

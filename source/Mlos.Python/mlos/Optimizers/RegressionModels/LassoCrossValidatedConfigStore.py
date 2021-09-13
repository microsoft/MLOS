#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from enum import Enum

from mlos.Spaces import SimpleHypergrid, ContinuousDimension, DiscreteDimension, CategoricalDimension, Point
from mlos.Spaces.Configs.ComponentConfigStore import ComponentConfigStore


class Selection(Enum):
    """
    Parameter to sklearn LassoCV regressor controlling how model coefficients are selected for update.
    From  https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LassoCV.html:
    If set to ‘random’, a random coefficient is updated every iteration rather than looping
    over features sequentially by default. This (setting to ‘random’) often leads to significantly
    faster convergence especially when tol is higher than 1e-4.
    """
    CYCLIC = 'cyclic'
    RANDOM = 'random'


lasso_cross_validated_config_store = ComponentConfigStore(
    parameter_space=SimpleHypergrid(
        name="lasso_regression_model_config",
        dimensions=[
            ContinuousDimension(name="eps", min=0, max=10.0 ** -3),
            DiscreteDimension(name="num_alphas", min=0, max=200),
            CategoricalDimension(name="fit_intercept", values=[False, True]),
            CategoricalDimension(name="normalize", values=[False, True]),
            CategoricalDimension(name="precompute", values=[False, True]),
            DiscreteDimension(name="max_iter", min=100, max=5 * 10 ** 3),
            ContinuousDimension(name="tol", min=0, max=1.0),
            CategoricalDimension(name="copy_x", values=[False, True]),
            DiscreteDimension(name="num_cross_validations", min=2, max=10),
            CategoricalDimension(name="verbose", values=[False, True]),
            DiscreteDimension(name="num_jobs", min=1, max=2),
            CategoricalDimension(name="positive", values=[False, True]),
            CategoricalDimension(name="selection", values=[selection.value for selection in Selection])
        ]
    ),
    default=Point(
        eps=10 ** -6,
        num_alphas=100,
        fit_intercept=False,
        normalize=False,
        # sklearn model expects precompute type str, bool, array-like, so setting to sklearn's default and excluding their list option
        precompute=False,
        max_iter=2000,
        tol=10 ** -4,
        copy_x=True,
        num_cross_validations=5,
        verbose=False,
        num_jobs=1,
        positive=False,
        selection=Selection.CYCLIC.value
    ),
    description="Wrapper for sklearn.linear_model.Lasso model."
                "This wrapper includes optional CV grid search to tune Lasso hyper parameters within each fit."
)

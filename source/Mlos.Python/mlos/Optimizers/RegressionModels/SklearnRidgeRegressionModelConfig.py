#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from enum import Enum

from mlos.Spaces import SimpleHypergrid, \
    ContinuousDimension, DiscreteDimension, CategoricalDimension, Point

from .RegressionModel import RegressionModelConfig


class SklearnRidgeRegressionModelConfig(RegressionModelConfig):
    class Solver(Enum):
        """
        From https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.Ridge.html:
        Solver to use in the computational routines:
            * ‘auto’ chooses the solver automatically based on the type of data.
            * ‘svd’ uses a Singular Value Decomposition of X to compute the Ridge coefficients. More stable for
                singular matrices than ‘cholesky’.
            * ‘cholesky’ uses the standard scipy.linalg.solve function to obtain a closed-form solution.
            * ‘sparse_cg’ uses the conjugate gradient solver as found in scipy.sparse.linalg.cg.
                As an iterative algorithm, this solver is more appropriate than ‘cholesky’ for
                large-scale data (possibility to set tol and max_iter).
            * ‘lsqr’ uses the dedicated regularized least-squares routine scipy.sparse.linalg.lsqr.
                It is the fastest and uses an iterative procedure.
            * ‘sag’ uses a Stochastic Average Gradient descent, and ‘saga’ uses its improved,
                unbiased version named SAGA. Both methods also use an iterative procedure, and are
                often faster than other solvers when both n_samples and n_features are large.
                Note that ‘sag’ and ‘saga’ fast convergence is only guaranteed on features with
                approximately the same scale. You can preprocess the data with a scaler from sklearn.preprocessing.

        All last five solvers support both dense and sparse data. However, only ‘sag’ and ‘sparse_cg’ supports
        sparse input when fit_intercept is True.
        """
        AUTO = 'auto'  # default
        SVD = 'svd'
        CHOLESKY = 'cholesky'
        LSQR = 'lsqr'
        SPARSE_CG = 'sparse_cg'
        SAG = 'sag'
        SAGA = 'saga'

    CONFIG_SPACE = SimpleHypergrid(
        name="sklearn_ridge_regression_model_config",
        dimensions=[
            ContinuousDimension(name="alpha", min=0, max=2 ** 16),
            CategoricalDimension(name="fit_intercept", values=[False, True]),
            CategoricalDimension(name="normalize", values=[False, True]),
            CategoricalDimension(name="copy_x", values=[False, True]),
            DiscreteDimension(name="max_iter", min=0, max=10 ** 5),
            ContinuousDimension(name="tol", min=0, max=2 ** 10),
            CategoricalDimension(name="solver", values=[solver.value for solver in Solver]),
        ]
    )
    _DEFAULT = Point(
        alpha=1.0,
        fit_intercept=True,
        normalize=False,
        copy_x=True,
        max_iter=1000,
        tol=10 ** -4,
        solver=Solver.AUTO.value
    )

    @classmethod
    def contains(cls, config):
        return Point(
            alpha=config.alpha,
            fit_intercept=config.fit_intercept,
            normalize=config.normalize,
            copy_x=config.copy_x,
            max_iter=config.max_iter,
            tol=config.tol,
            random_state=config.random_state,
            solver=config.solver
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
            copy_x=_DEFAULT.copy_x,
            max_iter=_DEFAULT.max_iter,
            tol=_DEFAULT.tol,
            random_state=None,
            solver=_DEFAULT.solver
    ):
        """
        Ridge parameters:
        :param alpha:Regularization strength; must be a positive float. Defaults to 1.0.
        :param fit_intercept: Whether to calculate the intercept for this model.
        :param normalize: This parameter is ignored when ``fit_intercept`` is set to False.
            If True, the regressors X will be normalized before regression by
            subtracting the mean and dividing by the l2-norm.
        :param copy_x: If ``True``, X will be copied; else, it may be overwritten.
        :param max_iter: The maximum number of iterations
        :param tol: The tolerance for the optimization: if the updates are
            smaller than ``tol``, the optimization code checks the
            dual gap for optimality and continues until it is smaller
            than ``tol``.
        :param solver: Solver to use in the computational routines:
            - 'auto' chooses the solver automatically based on the type of data.
            - 'svd' uses a Singular Value Decomposition of X to compute the Ridge
              coefficients. More stable for singular matrices than 'cholesky'.
            - 'cholesky' uses the standard scipy.linalg.solve function to
              obtain a closed-form solution.
            - 'sparse_cg' uses the conjugate gradient solver as found in
              scipy.sparse.linalg.cg. As an iterative algorithm, this solver is
              more appropriate than 'cholesky' for large-scale data
              (possibility to set `tol` and `max_iter`).
            - 'lsqr' uses the dedicated regularized least-squares routine
              scipy.sparse.linalg.lsqr. It is the fastest and uses an iterative
              procedure.
            - 'sag' uses a Stochastic Average Gradient descent, and 'saga' uses
              its improved, unbiased version named SAGA. Both methods also use an
              iterative procedure, and are often faster than other solvers when
              both n_samples and n_features are large. Note that 'sag' and
              'saga' fast convergence is only guaranteed on features with
              approximately the same scale. You can preprocess the data with a
              scaler from sklearn.preprocessing.
        :param random_state: The seed of the pseudo random number generator that selects a random
            feature to update. Used when ``selection`` == 'random'.
        """
        self.alpha = alpha
        self.fit_intercept = fit_intercept
        self.normalize = normalize
        self.copy_x = copy_x
        self.max_iter = max_iter
        self.tol = tol
        self.random_state = random_state
        self.solver = solver

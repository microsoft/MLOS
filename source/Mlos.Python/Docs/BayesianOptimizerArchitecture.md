# Bayesian Optimizer Architecture

## Components

1. [Surrogate Models](#surrogate-models)
2. [Utility Functions](#TODO)
3. [Numeric Optimizers](#TODO)
4. [Experiment Designer](#TODO)
5. [Bayesian Optimizer](#TODO)

## Other Classes

1. [Hypergrids](#hypergrids)
1. [Optimization Problems](#optimization-problems)

## Hypergrids

Hypergrids are used to describe multidimensional spaces comprized of Continuous, Discrete, Ordinal, or Categorical dimensions.

All optimizers we have reviewed to date ([Hypermapper](https://github.com/luinardi/hypermapper), [SMAC](https://github.com/automl/SMAC3), [bayesopt](https://github.com/rmcantin/bayesopt), and [scikit-learn](https://github.com/scikit-learn/scikit-learn)) optimizers implement their own notion of a search space.

Hypergrids are meant to provide a superset of their functionalities.
They further allow us to express hierarchical search spaces, where some parameters only become meaningful if some other parameter (e.g. a boolean flag) is set.

## Optimization Problems

`OptimizationProblem` is a class describing:

* The parameter space (aka decision variables) - represented as a Hypergrid of all allowed parameter values.
* The objective space - represented as a Hypergrid of all objectives we may wish to optimize
* The context space (akin to controlled variables)

## Surrogate Models

The role of surrogate models is to use parameter values and context values to predict performance metrics.

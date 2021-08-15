#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from collections import namedtuple
from typing import List, Tuple

import pandas as pd
import numpy as np

from mlos.Spaces import SimpleHypergrid, CategoricalDimension, Dimension


class Objective:
    def __init__(self, name: str, minimize: bool):
        self.name = name
        self.minimize = minimize


class SeriesMatchingObjective(Objective):
    def __init__(
        self, name: str,
        target_series_df: pd.DataFrame,
        series_domain_dimension: Dimension,
        series_codomain_dimension: Dimension,
        series_difference_metric: str
    ):
        self.name = name
        self.minimize = True  # This will always want to minimize error in order to match the function
        self.target_series_df = target_series_df
        self.series_domain_dimension = series_domain_dimension
        self.series_codomain_dimension = series_codomain_dimension
        self.series_difference_metric = series_difference_metric
        assert self.series_difference_metric in ["sum_of_squared_errors", "dynamic_time_warping", "cosine_similarity"]


def objective_to_dict(objective: Objective):
    if type(objective) is SeriesMatchingObjective:
        return {
            "name": objective.name,
            "minimize": objective.minimize,
            "target_series_df": objective.target_series_df,
            "series_domain_dimension": objective.series_domain_dimension,
            "series_codomain_dimension": objective.series_codomain_dimension,
            "series_difference_metric": objective.series_difference_metric
        }
    else:
        return {
            "name": objective.name,
            "minimize": objective.minimize
        }


def objective_from_dict(objective_dict: dict):
    if "target_series_df" in objective_dict:  # Test if objective_dict is of type SeriesMatchingObjective
        return SeriesMatchingObjective(
            name=objective_dict["name"],
            minimize=objective_dict["minimize"],
            target_series_df=objective_dict["target_series_df"],
            series_domain_dimension=objective_dict["series_domain_dimension"],
            series_codomain_dimension=objective_dict["series_codomain_dimension"],
            series_difference_metric=objective_dict["series_difference_metric"]
        )
    else:
        return Objective(
            name=objective_dict["name"],
            minimize=objective_dict["minimize"]
        )


class OptimizationProblem:
    """Models an instance of an optimization problem.

    An instance of OptimizationProblem can be used to create a variety of optimizers and instantly enlighten them to
    what they are working with.

    Many optimization problems contain the same set of elements:
    1. Decision Variables / Search Space - decision variables characterized by their allowed ranges and constraints form a Search Space.
    2. Objectives - one or more values to optimize. Each objective is meant to be either maximized or minimized.
    3. Context - this represents either: 1. controlled variables in an active learning scenarios, or 2. context information in an online learning scenario.

    For example if we are attempting to optimize a smart cache:

    Decision variables:
        * cache implementation (array, hashmap), each implementation's parameters:
            * array: size, associativity, eviction policy
            * hashmap: size, hash function, bucket data structure, bucket size, bucket eviction policy

    Objectives:
        * latency
        * cache memory footprint
        * recomputation cost (averge, median, total)
        * hit ratio
        * cache utilization

    Context:
        * workload characteristics:
            * true working set size (only known in active learning scenario)
            * estimated working set size (possibly many estimators, many Confidence Interval sizes)
            * recomputation cost distribution (true or estimated)

        * deployment context:
            * machine characteristics:
                * num cores
                * amount of ram
                * disk type
            * runtime state:
                * cpu utilization
                * ram utilization
                * etc

    Parameters
    ----------
    parameter_space : Hypergrid
        Input parameter space for objective, i.e. the search space.
    objective_space : Hypergrid(
        Output space for the objective, can be (-inf, +inf)
    objectives : list[Objective]
        Objective function(s) to optimize, with input from parameter_space and output in objective_space.
    context_space : Hypergrid, default=None
        Additional run-time context features.

    Attributes
    ----------
    feature_space : Hypergrid
        Joint space of parameters and context.
    """

    # The dimensions that we inject to keep track of individual subspaces, but which are worthless
    # for modeling purposes.
    META_DIMENSION_NAMES = {"contains_parameters", "contains_context", "contains_objectives"}

    def __init__(
            self,
            parameter_space: SimpleHypergrid,
            objective_space: SimpleHypergrid,
            objectives: List[Objective],
            context_space: SimpleHypergrid = None,
    ):
        self.parameter_space = parameter_space
        self.context_space = context_space

        assert not any(isinstance(dimension, CategoricalDimension) for dimension in objective_space.dimensions), "Objective dimension cannot be Categorical."
        objective_dimension_names = {dimension.name for dimension in objective_space.dimensions}
        assert all(objective.name in objective_dimension_names for objective in objectives), "All objectives must belong to objective space."
        self.objective_space = objective_space
        # We need to keep track of which objective to minimize, and which one to maximize.
        self.objectives = objectives
        self.objective_names = [objective.name for objective in self.objectives]


        # Fit functions / surrogate models will be fed features consisting of both context and parameters.
        # Thus, the feature space is comprised of both context and parameters.
        has_context = self.context_space is not None
        self.feature_space = SimpleHypergrid(
            name="features",
            dimensions=[
                CategoricalDimension(name="contains_context", values=[has_context])
            ]
        ).join(
            subgrid=self.parameter_space,
            on_external_dimension=CategoricalDimension(name="contains_context", values=[has_context])
        )
        if has_context:
            self.feature_space = self.feature_space.join(
                subgrid=self.context_space,
                on_external_dimension=CategoricalDimension(name="contains_context", values=[True])
            )

    def construct_feature_dataframe(self, parameters_df: pd.DataFrame, context_df: pd.DataFrame = None, product: bool = False):
        """Construct feature value dataframe from config value and context value dataframes.

        If product is True, creates a cartesian product, otherwise appends columns.

        """
        if (self.context_space is not None) and (context_df is None):
            raise ValueError("Context required by optimization problem but not provided.")

        # prefix column names to adhere to dimensions in hierarchical hypergrid
        #
        features_df = parameters_df.rename(lambda x: f"{self.parameter_space.name}.{x}", axis=1)
        if context_df is not None and len(context_df) > 0:
            # Context_space can be none for time-series-only fitting
            #
            if self.context_space is None:
                renamed_context_values = context_df.rename(lambda x: f"series_context_space.{x}", axis=1)
            else:
                renamed_context_values = context_df.rename(lambda x: f"{self.context_space.name}.{x}", axis=1)
            features_df['contains_context'] = True
            if product:
                renamed_context_values['contains_context'] = True
                features_df = features_df.merge(renamed_context_values, how='outer', on='contains_context')
                features_df.index = parameters_df.index.copy()
            else:
                if len(parameters_df) != len(context_df):
                    raise ValueError(f"Incompatible shape of parameters and context: {parameters_df.shape} and {context_df.shape}.")
                features_df = pd.concat([features_df, renamed_context_values], axis=1)

        else:
            features_df['contains_context'] = False
        return features_df

    def deconstruct_feature_dataframe(self, features_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Splits the feature dataframe back into parameters and context dataframes.

        This is a workaround. What we should really do is implement this functionality as a proper operator on Hypergrids.
        """
        parameter_column_names_mapping = {
            f"{self.parameter_space.name}.{dimension_name}": dimension_name
            for dimension_name
            in self.parameter_space.dimension_names
        }
        existing_parameter_names = [parameter_name for parameter_name in parameter_column_names_mapping.keys() if parameter_name in features_df.columns]
        parameters_df = features_df[existing_parameter_names]
        parameters_df.rename(columns=parameter_column_names_mapping, inplace=True)

        if self.context_space is not None:
            context_column_names_mapping = {
                f"{self.context_space.name}.{dimension_name}": dimension_name
                for dimension_name
                in self.context_space.dimension_names
            }
            existing_context_column_names = [column_name for column_name in context_column_names_mapping.keys() if column_name in features_df.columns]
            context_df = features_df[existing_context_column_names]
            context_df.rename(columns=context_column_names_mapping, inplace=True)
        else:
            context_df = None

        return parameters_df, context_df

    def to_dict(self):
        return {
            "parameter_space": self.parameter_space,
            "context_space": self.context_space,
            "objective_space": self.objective_space,
            "objectives": [objective_to_dict(objective) for objective in self.objectives]
        }

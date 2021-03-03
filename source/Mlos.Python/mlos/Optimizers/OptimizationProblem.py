#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from collections import namedtuple
import json
from typing import List, Tuple

import pandas as pd

from mlos.Grpc import OptimizerService_pb2
from mlos.Spaces import Hypergrid, SimpleHypergrid, CategoricalDimension
from mlos.Spaces.HypergridsJsonEncoderDecoder import HypergridJsonDecoder, HypergridJsonEncoder

Objective = namedtuple("Objective", ["name", "minimize"])

def objective_to_dict(objective):
    return {
        "name": objective.name,
        "minimize": objective.minimize
    }

def objective_from_dict(objective_dict):
    return Objective(**objective_dict)

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
            parameter_space: Hypergrid,
            objective_space: Hypergrid,
            objectives: List[Objective],
            context_space: Hypergrid = None,
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

    def to_protobuf(self):
        """ Serializes self to a protobuf.

        :return:
        """
        return OptimizerService_pb2.OptimizationProblem(
            ParameterSpace=OptimizerService_pb2.Hypergrid(HypergridJsonString=json.dumps(self.parameter_space, cls=HypergridJsonEncoder)),
            ObjectiveSpace=OptimizerService_pb2.Hypergrid(HypergridJsonString=json.dumps(self.objective_space, cls=HypergridJsonEncoder)),
            Objectives=[OptimizerService_pb2.Objective(Name=objective.name, Minimize=objective.minimize) for objective in self.objectives],
            ContextSpace=None if self.context_space is None
            else OptimizerService_pb2.Hypergrid(HypergridJsonString=json.dumps(self.context_space, cls=HypergridJsonEncoder))
        )

    @classmethod
    def from_protobuf(cls, optimization_problem_pb2: OptimizerService_pb2.OptimizationProblem):
        """ Builds an optimization problem from protobufs.

        :param optimization_problem_pb2:
        :return:
        """
        return OptimizationProblem(
            parameter_space=json.loads(optimization_problem_pb2.ParameterSpace.HypergridJsonString, cls=HypergridJsonDecoder),
            objective_space=json.loads(optimization_problem_pb2.ObjectiveSpace.HypergridJsonString, cls=HypergridJsonDecoder),
            objectives=[
                Objective(name=objective_pb2.Name, minimize=objective_pb2.Minimize)
                for objective_pb2 in optimization_problem_pb2.Objectives
            ],
            context_space=None if not optimization_problem_pb2.ContextSpace.HypergridJsonString
            else json.loads(optimization_problem_pb2.ContextSpace.HypergridJsonString, cls=HypergridJsonDecoder)
        )

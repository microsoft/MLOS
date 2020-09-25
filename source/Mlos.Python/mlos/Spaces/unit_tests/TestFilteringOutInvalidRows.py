#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import os
import unittest
import warnings

import pandas as pd

import mlos.global_values as global_values
from mlos.Logger import create_logger
from mlos.Optimizers.BayesianOptimizer import bayesian_optimizer_config_store
from mlos.Optimizers.ExperimentDesigner.UtilityFunctionOptimizers.GlowWormSwarmOptimizer import glow_worm_swarm_optimizer_config_store
from mlos.Spaces import ContinuousDimension, DiscreteDimension, Point
from mlos.Tracer import Tracer, trace, traced

class TestFilteringOutInvalidRows(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Sets up all the singletons needed to test the BayesianOptimizer.

        """
        warnings.simplefilter("error")
        global_values.declare_singletons()
        global_values.tracer = Tracer(actor_id=cls.__name__, thread_id=0)
        cls.logger = create_logger(logger_name=cls.__name__)

    @classmethod
    def tearDownClass(cls) -> None:
        temp_dir = os.path.join(os.getcwd(), "temp")
        if not os.path.exists(temp_dir):
            os.mkdir(temp_dir)
        trace_output_path = os.path.join(temp_dir, f"{cls.__name__}.json")
        print(f"Dumping trace to {trace_output_path}")
        global_values.tracer.dump_trace_to_file(output_file_path=trace_output_path)

    def test_filtering_out_invalid_rows(self):
        spaces = [
            bayesian_optimizer_config_store.parameter_space,
            glow_worm_swarm_optimizer_config_store.parameter_space
        ]

        # Just to make sure we are testing both hierarchical and flat code paths.
        #
        self.assertTrue(any(space.is_hierarchical() for space in spaces))
        self.assertTrue(any(not space.is_hierarchical() for space in spaces))

        num_samples = 1000
        for space in spaces:
            random_dataframe_with_invalid_rows = space.random_dataframe(num_samples=num_samples)
            for dimension in space.dimensions:
                if isinstance(dimension, (ContinuousDimension, DiscreteDimension)):
                    # This makes about half of the rows invalid.
                    #
                    random_dataframe_with_invalid_rows.loc[:, [dimension.name]] *= 2
                    break

            with traced(scope_name="slow_filtering"):
                # Let's filter out invalid rows the slow way.
                #
                valid_indices = []
                for idx in random_dataframe_with_invalid_rows.index:
                    row_as_df = random_dataframe_with_invalid_rows.loc[[idx]]
                    row_as_point = Point.from_dataframe(row_as_df)
                    if row_as_point in space:
                        valid_indices.append(idx)
                expected_valid_rows_index = pd.Index(valid_indices)

            print(f"{len(expected_valid_rows_index)}/{len(random_dataframe_with_invalid_rows.index)} rows are valid.")
            self.assertTrue(0 < len(expected_valid_rows_index))
            self.assertTrue(len(expected_valid_rows_index) < num_samples)

            # Let's filter out invalid rows the fast way.
            #
            actual_valid_rows_index = space.filter_out_invalid_rows(original_dataframe=random_dataframe_with_invalid_rows, exclude_extra_columns=True).index
            self.assertTrue(expected_valid_rows_index.equals(actual_valid_rows_index))

            if not space.is_hierarchical():
                # For flat spaces we can choose between the column-wise operators and the row-wise validation. This is to get the tracing data to see the
                # perf difference, but also to validate correctness by computing the desired index in yet another way.
                #
                with traced(scope_name="faster_filtering"):
                    expected_valid_rows_index_2 = random_dataframe_with_invalid_rows[random_dataframe_with_invalid_rows.apply(
                        lambda row: Point(**{dim_name: row[i] for i, dim_name in enumerate(space.dimension_names)}) in space,
                        axis=1
                    )].index
                self.assertTrue(expected_valid_rows_index_2.equals(actual_valid_rows_index))




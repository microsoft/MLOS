#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import random
import unittest

from mlos.Spaces.Dimensions.ContinuousDimension import ContinuousDimension
from mlos.Spaces.Dimensions.DiscreteDimension import DiscreteDimension

from mlos.Spaces.SimpleHypergrid import SimpleHypergrid


class TestSimpleSpaces(unittest.TestCase):

    def setUp(self) -> None:
        self.small_square = SimpleHypergrid(
            name="small_square",
            dimensions=[
                ContinuousDimension(name='x', min=1, max=2),
                ContinuousDimension(name='y', min=1, max=2)
            ]
        )

        self.big_square = SimpleHypergrid(
            name="big_square",
            dimensions=[
                ContinuousDimension(name='x', min=0, max=3),
                ContinuousDimension(name='y', min=0, max=3)
            ]
        )

        self.small_grid = SimpleHypergrid(
            name="small_grid",
            dimensions=[
                DiscreteDimension(name='x', min=1, max=2),
                DiscreteDimension(name='y', min=1, max=2)
            ]
        )

        self.big_grid = SimpleHypergrid(
            name="big_grid",
            dimensions=[
                DiscreteDimension(name='x', min=0, max=3),
                DiscreteDimension(name='y', min=0, max=3),
                DiscreteDimension(name='z', min=0, max=3)
            ]
        )

        self.all_grids = [
            self.small_square,
            self.big_square,
            self.small_grid,
            self.big_grid,
        ]

    def test_simple_hypergrid(self):

        self.assertTrue(self.big_square.contains_space(self.small_square))
        self.assertFalse(self.small_square.contains_space(self.big_square))
        self.assertTrue(self.big_grid.contains_space(self.small_grid))
        self.assertFalse(self.small_grid.contains_space(self.big_grid))

        self.assertTrue(self.small_square.contains_space(self.small_grid))
        self.assertFalse(self.small_grid.contains_space(self.small_square))

        self.assertFalse(self.big_square.contains_space(self.big_grid))

    def test_random_point_generation(self):
        for grid in self.all_grids:
            for _ in range(100):
                self.assertTrue(grid.random() in grid)

    def test_reseeding_random_state(self):
        """ Validates that we can generate the same sequence of random points.

        :return:
        """
        for grid in self.all_grids:
            for i in range(10):

                # Let's seed the grid for the first time
                random_state = random.Random()
                random_state.seed(i)
                grid.random_state = random_state
                first_pass_points = [grid.random() for _ in range(100)]

                # Let's reseed it
                random_state = random.Random()
                random_state.seed(i)
                grid.random_state = random_state
                second_pass_points = [grid.random() for _ in range(100)]

                # let's make sure they match up
                for first_pass_point, second_pass_point in zip(first_pass_points, second_pass_points):
                    self.assertTrue(first_pass_point == second_pass_point)


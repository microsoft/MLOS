#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import unittest

from mlos.Spaces.Dimensions.CategoricalDimension import CategoricalDimension


class TestCategoricalDimension(unittest.TestCase):


    def test_categorical_dimension_api(self):
        """ Making sure that all functions are implemented and behave sanely.

        :return:
        """
        warm_colors = CategoricalDimension(
            name='colors',
            values=[
                'red',
                'yellow',
                'orange',
            ]
        )

        cool_colors = CategoricalDimension(
            name='colors',
            values=[
                'green',
                'blue',
                'indigo',
                'violet',
            ]
        )

        rainbow_colors = CategoricalDimension(
            name='colors',
            values=[
                'infra-red',
                'red',
                'orange',
                'yellow',
                'green',
                'blue',
                'indigo',
                'violet',
                'ultra-violet',
            ]
        )

        self.assertTrue(warm_colors in rainbow_colors)
        self.assertTrue(cool_colors in rainbow_colors)
        self.assertTrue(warm_colors.union(cool_colors) in rainbow_colors)
        self.assertFalse(rainbow_colors in warm_colors.union(cool_colors))
        self.assertTrue('infra-red' in rainbow_colors)
        self.assertTrue('infra-red' in rainbow_colors - warm_colors - cool_colors)
        self.assertTrue('red' not in rainbow_colors - warm_colors)
        self.assertTrue(warm_colors.intersects(rainbow_colors))
        self.assertFalse(warm_colors.intersects(cool_colors))
        self.assertTrue(rainbow_colors.intersection(warm_colors) == warm_colors)
        self.assertTrue(len(rainbow_colors - warm_colors - cool_colors) == 2)
        self.assertTrue(all(color in rainbow_colors for color in warm_colors.linspace()))








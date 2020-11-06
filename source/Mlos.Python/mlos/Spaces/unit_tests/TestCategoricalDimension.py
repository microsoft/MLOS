#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#

from mlos.Spaces.Dimensions.CategoricalDimension import CategoricalDimension


class TestCategoricalDimension:


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

        assert warm_colors in rainbow_colors
        assert cool_colors in rainbow_colors
        assert warm_colors.union(cool_colors) in rainbow_colors
        assert not rainbow_colors in warm_colors.union(cool_colors)
        assert 'infra-red' in rainbow_colors
        assert 'infra-red' in rainbow_colors - warm_colors - cool_colors
        assert 'red' not in rainbow_colors - warm_colors
        assert warm_colors.intersects(rainbow_colors)
        assert not warm_colors.intersects(cool_colors)
        assert rainbow_colors.intersection(warm_colors) == warm_colors
        assert len(rainbow_colors - warm_colors - cool_colors) == 2
        assert all(color in rainbow_colors for color in warm_colors.linspace())








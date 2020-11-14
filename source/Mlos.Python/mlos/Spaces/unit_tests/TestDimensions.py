#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import math
import random
import pytest

import mlos.Spaces.Dimensions.DimensionCalculator
from mlos.Spaces.Dimensions.ContinuousDimension import ContinuousDimension
from mlos.Spaces.Dimensions.DiscreteDimension import DiscreteDimension
from mlos.Spaces.Dimensions.OrdinalDimension import OrdinalDimension
from mlos.Spaces.Dimensions.CategoricalDimension import CategoricalDimension


def fibonacci(max, one_ago=0, next=1):
    while next <= max:
        yield next
        one_ago, next = next, one_ago + next


class TestContinuousDimension:

    def setup_method(self, method):
        self.empty = ContinuousDimension(name='x', min=0, max=0, include_min=False, include_max=False)
        self.unbounded_continuous = ContinuousDimension(name='x', min=0, max=math.inf)
        self.unbounded_discrete = DiscreteDimension(name='x', min=0, max=math.inf)
        self.should_be_empty = ContinuousDimension(name='x', min=0, max=0, include_min=False, include_max=True)
        self.should_be_empty_too = ContinuousDimension(name='x', min=0, max=0, include_min=True, include_max=False)
        self.should_contain_zero = ContinuousDimension(name='x', min=0, max=0, include_min=True, include_max=True)
        self.closed = ContinuousDimension(name='x', min=0, max=1)
        self.left_open = ContinuousDimension(name='x', min=0, max=1, include_min=False)
        self.right_open = ContinuousDimension(name='x', min=0, max=1, include_max=False)
        self.open = ContinuousDimension(name='x', min=0, max=1, include_min=False, include_max=False)
        self.inner = ContinuousDimension(name='x', min=0.2, max=0.8)
        self.outer = ContinuousDimension(name='x', min=-0.2, max=1.2)
        self.left_overlapping = ContinuousDimension(name='x', min=-0.2, max=0.8)
        self.right_overlapping = ContinuousDimension(name='x', min=0.2, max=1.2)
        self.inner_wrongly_named = ContinuousDimension(name='y', min=0.2, max=0.8)
        self.one_to_five = ContinuousDimension(name='x', min=1, max=5)
        self.six_to_ten = ContinuousDimension(name='x', min=6, max=10)

    def test_string_representation(self):
        assert str(self.empty) == "x: (0.00, 0.00)"
        assert str(self.should_be_empty) == "x: (0.00, 0.00)"
        assert str(self.should_be_empty_too) == "x: (0.00, 0.00)"
        assert str(self.should_contain_zero) == "x: [0.00, 0.00]"
        assert str(self.closed) == "x: [0.00, 1.00]"
        assert str(self.left_open) == "x: (0.00, 1.00]"
        assert str(self.right_open) == "x: [0.00, 1.00)"
        assert str(self.open) == "x: (0.00, 1.00)"
        assert str(self.inner) == "x: [0.20, 0.80]"
        assert str(self.outer) == "x: [-0.20, 1.20]"
        assert str(self.left_overlapping) == "x: [-0.20, 0.80]"
        assert str(self.right_overlapping) == "x: [0.20, 1.20]"
        assert str(self.inner_wrongly_named) == "y: [0.20, 0.80]"

    def test_point_containment(self):

        assert (
            0 not in self.empty
            and 0 not in self.should_be_empty
            and 0 not in self.should_be_empty_too
            and 0 in self.should_contain_zero
        )

        assert (
            -1 not in self.closed
            and -1 not in self.left_open
            and -1 not in self.right_open
            and -1 not in self.open
        )

        assert (
            0 in self.closed
            and 0 not in self.left_open
            and 0 in self.right_open
            and 0 not in self.open
        )

        assert (
            0.5 in self.closed
            and 0.5 in self.left_open
            and 0.5 in self.right_open
            and 0.5 in self.open
        )

        assert (
            1 in self.closed
            and 1 in self.left_open
            and 1 not in self.right_open
            and 1 not in self.open
        )

        assert (
            2 not in self.closed
            and 2 not in self.left_open
            and 2 not in self.right_open
            and 2 not in self.open
        )

    def test_continuous_dimension_containment(self):
        assert self.open in self.closed
        assert self.left_open in self.closed
        assert self.right_open in self.closed

        assert self.left_open not in self.open
        assert self.right_open not in self.open
        assert self.closed not in self.open

        assert self.left_open not in self.right_open
        assert self.right_open not in self.left_open

        assert self.inner in self.closed
        assert self.inner in self.open
        assert self.inner in self.left_open
        assert self.inner in self.right_open

        assert self.closed in self.outer
        assert self.open in self.outer
        assert self.left_open in self.outer
        assert self.right_open in self.outer

        assert self.inner_wrongly_named not in self.closed
        assert self.inner_wrongly_named not in self.open
        assert self.inner_wrongly_named not in self.left_open
        assert self.inner_wrongly_named not in self.right_open

    def test_continuous_dimension_set_operations(self):
        assert self.inner in self.inner.union(self.closed)
        assert self.inner in self.inner.intersection(self.closed)

        assert self.open in self.open.intersection(self.closed)
        assert self.closed not in self.open.intersection(self.closed)
        assert self.closed in self.open.union(self.closed)
        assert self.closed in self.left_open.union(self.right_open)
        assert self.left_open.intersection(self.right_open) in self.open

    def test_random(self):
        with pytest.raises(ValueError):
            self.empty.random()
        with pytest.raises(ValueError):
            self.unbounded_continuous.random()
        with pytest.raises(OverflowError):
            self.unbounded_discrete.random()

        assert self.outer.random() in self.outer
        for _ in range(1000):
            assert self.one_to_five.random() not in self.six_to_ten


class TestCompositeDimension:

    def test_union_of_continuous_dimensions(self):
        A = ContinuousDimension(name='x', min=0, max=1)
        B = ContinuousDimension(name='x', min=2, max=3)
        C = A.union(B)
        assert 0.5 in C
        assert 2.5 in C
        assert 1.5 not in C

    def test_arbitrary_composition_of_continuous_dimensions(self):
        A = ContinuousDimension(name='x', min=0, max=1)
        B = ContinuousDimension(name='x', min=2, max=3)
        C = ContinuousDimension(name='x', min=2.5, max=3.5)
        D = A.union(B) - C
        E = B - C
        F = A.union(E)

        assert 0.5 in D
        assert 1.5 not in D
        assert 2.5 not in D
        assert 3.4 not in D
        assert 35 not in D
        assert 2 in E
        assert 2.5 not in E
        assert 0 in F and 1 in F and 1.5 not in F and 2 in F and 2.5 not in F

    def test_composition_of_arbitrary_dimensions(self):
        C1 = ContinuousDimension(name='x', min=0, max=1)
        C2 = ContinuousDimension(name='x', min=1, max=2)
        C3 = C1 - C2
        D = DiscreteDimension(name='x', min=0, max=1)

        with pytest.raises(TypeError):
            C1.intersection(D)
        with pytest.raises(TypeError):
            C3.intersection(D)
        with pytest.raises(TypeError):
            D.intersection(C1)

class TestDiscreteDimension:

    def setup_method(self, method):
        self.just_one = DiscreteDimension(name='x', min=1, max=1)
        self.one_two = DiscreteDimension(name='x', min=1, max=2)
        self.one_two_three = DiscreteDimension(name='x', min=1, max=3)
        self.one_two_three_four = DiscreteDimension(name='x', min=1, max=4)
        self.one_to_hundred = DiscreteDimension(name='x', min=1, max=100)

        self.all_dims = [
            self.just_one,
            self.one_two,
            self.one_two_three,
            self.one_two_three_four,
            self.one_to_hundred,
        ]

    def test_string_representation(self):
        assert str(self.just_one) == "x: {1}"
        assert str(self.one_two) == "x: {1, 2}"
        assert str(self.one_two_three) == "x: {1, 2, 3}"
        assert str(self.one_two_three_four) == "x: {1, 2, ... , 4}"
        assert str(self.one_to_hundred) == "x: {1, 2, ... , 100}"

    def test_point_containment(self):
        assert 1 in self.just_one

    def test_discrete_dimension_containment(self):
        assert self.just_one in self.one_two
        assert self.just_one in self.one_two_three

    def test_discrete_dimension_set_operations(self):

        assert self.just_one not in self.one_two_three - self.one_two
        assert 1 in self.just_one.intersection(self.one_two).intersection(self.one_two_three)
        assert 1 not in self.just_one - self.just_one
        assert 42 not in self.just_one.union(self.just_one)


    def test_arbitrary_composition_of_discrete_dimensions(self):

        random.seed(1)
        for k in range(1, 10):
            # let's do random mixes of our dimensions and make sure they behave sanely
            unions = random.choices(self.all_dims, k=k)
            diffs = random.choices(self.all_dims, k=k)
            intersects = random.choices(self.all_dims, k=k)

            # let's put together the resulting set
            resulting_set = unions[0]
            for i in range(k):
                resulting_set = resulting_set.union(unions[i])
                resulting_set = resulting_set.difference(diffs[i])
                resulting_set = resulting_set.intersection(intersects[i])

            # now let's iterate over values in unions and make sure they belong
            for union in unions:
                for value in union.linspace():
                    # let's see if it should belong to the resulting_set
                    should_belong = False
                    for j in range(k):
                        should_belong = should_belong or (value in unions[j])
                        should_belong = should_belong and (value not in diffs[j])
                        should_belong = should_belong and (value in intersects[j])

                    if not should_belong == (value in resulting_set):
                        assert False

    def test_random(self):
        assert self.just_one.random() in self.just_one
        for _ in range(10):
            assert self.one_two.random() in self.one_two_three


class TestDimensions:
    def test_containment(self):
        long_segment = ContinuousDimension(name='x', min=0, max=100*1000)
        short_segment = ContinuousDimension(name='x', min=0, max=100)

        long_linear_sequence = DiscreteDimension(name='x', min=0, max=100*1000)
        short_linear_sequence = DiscreteDimension(name='x', min=0, max=100*1000)

        long_fibonacci_sequence = OrdinalDimension(
            name='x',
            ordered_values=[i for i in fibonacci(max=100*1000)],
            ascending=True
        )

        short_fibonacci_sequence = OrdinalDimension(
            name='x',
            ordered_values=[i for i in fibonacci(max=100)],
            ascending=True
        )

        a_few_options = CategoricalDimension(
            name='x',
            values=[5, 13, 34]
        )

        boolean_choice = CategoricalDimension(
            name='x',
            values=[True, False]
        )

        for dimension in [short_segment, long_linear_sequence, short_linear_sequence, long_fibonacci_sequence,
                          short_fibonacci_sequence, a_few_options]:
            assert dimension in long_segment

        assert short_fibonacci_sequence in long_fibonacci_sequence
        assert a_few_options in short_fibonacci_sequence
        assert True in boolean_choice
        assert 12 in long_segment

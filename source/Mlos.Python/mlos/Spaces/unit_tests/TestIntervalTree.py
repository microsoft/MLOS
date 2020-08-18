#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import random
import unittest

from mlos.Spaces.Dimensions.ContinuousDimension import ContinuousDimension
from mlos.Spaces.Dimensions.IntervalTree import IntervalTree

class TestIntervalTreeWithContinuousDimension(unittest.TestCase):
    """ Comprehensively tests all

    """

    def test_pop_overlapping_chunks(self):
        """ Exercises IntervalTree.pop_overlapping_chunks() method.

        """

        zero_to_one = ContinuousDimension(name='x', min=0, max=1)
        two_to_three = ContinuousDimension(name='x', min=2, max=3)
        five_to_seven = ContinuousDimension(name='x', min=5, max=7)
        minus_one_to_four = ContinuousDimension(name='x', min=-1, max=4)

        interval_tree = IntervalTree(name='x', chunks_type=ContinuousDimension)
        interval_tree.add(zero_to_one)
        interval_tree.add(two_to_three)
        interval_tree.add(five_to_seven)

        overlapping_chunks = interval_tree.pop_overlapping_chunks(chunk=minus_one_to_four)
        self.assertTrue(len(overlapping_chunks) == 2)
        for chunk in overlapping_chunks:
            self.assertTrue(chunk in (zero_to_one, two_to_three))

    def test_inserting_overlapping_chunks(self):
        zero_to_ten = ContinuousDimension(name='x', min=0, max=10)
        five_to_fifteen = ContinuousDimension(name='x', min=5, max=15)
        interval_tree = IntervalTree(name='x', chunks_type=ContinuousDimension)

        interval_tree.add(zero_to_ten)
        interval_tree.add(five_to_fifteen)

        only_node = interval_tree.root
        self.assertTrue(only_node.left is None)
        self.assertTrue(only_node.right is None)
        self.assertTrue(only_node.parent is None)
        resulting_chunk = only_node.payload
        self.assertTrue(resulting_chunk.min == 0)
        self.assertTrue(resulting_chunk.max == 15)

    def test_pop_overlapping_chunks_2(self):
        """ Exercises IntervalTree.pop_overlapping_chunks() method more throughly.

        Let's make a bunch of intervals, place them in the tree and then let's pop_overlappnig_chunks from the tree.

        To test the widest array of code paths, let's make a tree with a lot of evenly spaced intervals. Then, let's
        select one at random and produce intervals that should overlap.
        """
        random.seed(2)
        num_intervals_in_tree = 20
        intervals_width = 10
        gap_between_intervals = 1000
        intervals = []

        for i in range(num_intervals_in_tree):
            interval_min = i * (gap_between_intervals + intervals_width)
            interval_max = interval_min + intervals_width
            intervals.append(ContinuousDimension(name='x', min=interval_min, max=interval_max))

        # let's shuffle the intervals
        intervals = sorted(intervals, key=lambda interval: random.random())

        # Let's run a test suite for all intervals in the tree
        for i in range(num_intervals_in_tree):

            overlapping_interval = intervals[i]

            for possibly_overlapping_interval, overlaps \
                    in self.enumerate_possibly_overlapping_continuous_intervals(overlapping_interval, gap_width=gap_between_intervals):
                # we gotta make a new tree every time
                interval_tree = self.make_tree(intervals)
                overlapping_chunks = interval_tree.pop_overlapping_chunks(possibly_overlapping_interval)
                if overlaps:
                    self.assertTrue(overlapping_chunks[0] == overlapping_interval)
                else:
                    self.assertTrue(len(overlapping_chunks) == 0)


    def make_tree(self, intervals):
        name = 'x' if not intervals else intervals[0].name
        chunks_type = ContinuousDimension if not intervals else type(intervals[0])

        interval_tree = IntervalTree(name=name, chunks_type=chunks_type)
        for interval in intervals:
            interval_tree.add(interval)

        return interval_tree

    def enumerate_possibly_overlapping_continuous_intervals(self, interval, gap_width):
        """ For a given interval, enumerates a list of intervals and a boolean indicating overlap.

        """
        min_for_preceding_intervals = interval.min - gap_width / 2.0
        interval_width = (interval.max - interval.min)

        preceding = ContinuousDimension(
            name=interval.name,
            min=min_for_preceding_intervals,
            max=interval.min - gap_width / 3.0
        )
        yield preceding, False

        preceding_contiguous = ContinuousDimension(
            name=interval.name,
            min=min_for_preceding_intervals,
            max=interval.min,
            include_max=not interval.include_min
        )
        yield preceding, False

        if interval.include_min:
            preceding_overlapping_at_min = ContinuousDimension(
                name=interval.name,
                min=min_for_preceding_intervals,
                max=interval.min
            )
            yield preceding_overlapping_at_min, True

        overlapping_at_front = ContinuousDimension(
            name=interval.name,
            min=min_for_preceding_intervals,
            max=interval.min + interval_width / 2.0
        )
        yield overlapping_at_front, True

        contained = ContinuousDimension(
            name=interval.name,
            min=interval.min + interval_width / 3.0,
            max=interval.max + interval_width * 2.0 / 3.0
        )

        yield contained, True






class TestIntervalTreeWithDiscreteDimension(unittest.TestCase):
    pass
#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from .Dimension import Dimension
from .SortedBinaryTree import SortedBinaryTree, Node

class IntervalTree:
    """ Implements efficient algorithms on a sorted interval tree.

    The IntervalTree is a tree of Intervals (Dimensions) constructed in such a way that
    1) Constituent intervals can be enumerated
    2) No two constituent intervals overlap, nor are they contiguous
    3) We can efficiently test if:
        1) A number belongs to any interval in the tree
        2) An interval is fully contained by the tree
    """

    def __init__(self, name, chunks_type):
        self.name = name
        self.chunks_type = chunks_type
        self.sorted_binary_tree = SortedBinaryTree()

    def copy(self):
        copy = IntervalTree(name=self.name, chunks_type=self.chunks_type)
        copy.sorted_binary_tree = SortedBinaryTree()

        # By enumerating in PRE_ORDER we guarantee that the copy will have the same
        # tree shape.
        for node in self.sorted_binary_tree.enumerate(order=SortedBinaryTree.PRE_ORDER):
            key = node.key
            interval = node.payload
            copy.sorted_binary_tree.add(key=key, payload=interval.copy())
        return copy

    @property
    def root(self):
        return self.sorted_binary_tree.root

    @root.setter
    def root(self, dimension):
        assert isinstance(dimension, Dimension)
        self.sorted_binary_tree.root = Node(key=dimension.min, payload=dimension)

    def enumerate(self):
        return self.sorted_binary_tree.enumerate()

    def add(self, chunk):
        assert isinstance(chunk, self.chunks_type)
        overlapping_chunks = self.pop_overlapping_chunks(chunk)
        result = chunk
        for overlapping_chunk in overlapping_chunks:
            result = result.union(overlapping_chunk)
        self.sorted_binary_tree.add(key=result.min, payload=result)

    def push(self, chunk):
        """ Push the chunk onto the tree. Use with caution.

        Users of this method have to be certain that the chunk does not overlap nor is contiguous with any other chunks.
        Otherwise, some of the invariants might be violated and the tree will become corrupt.
        """
        self.sorted_binary_tree.add(key=chunk.min, payload=chunk)

    def remove(self, chunk):
        assert isinstance(chunk, self.chunks_type)
        overlapping_chunks = self.pop_overlapping_chunks(chunk)

        for overlapping_chunk in overlapping_chunks:
            if overlapping_chunk in chunk:
                # we have popped it successfully already
                continue
            # We need to do some math
            difference = overlapping_chunk.difference(chunk)
            self.push(difference)

    def pop_overlapping_chunks(self, chunk):
        """ Finds, removes, and returns an iterable of chunks overlapping with chunk.

        The purpose of this function is to make it easier to maintain the invariant
        that no two chunks in the IntervalTree overlap.

        """
        # PREMATURE OPTIMIZATION IS THE ROOT OF ALL EVIL - so let's do it the dumb way.
        # TODO: optimize to make O(log(n) + m) rather than O(n + m), where m is number of overlapping chunks
        nodes_to_pop = [
            node
            for node
            in self.sorted_binary_tree.enumerate()
            if node.payload.intersects(chunk)
        ]

        overlapping_chunks = [self.sorted_binary_tree.pop_node(node).payload for node in nodes_to_pop]
        return overlapping_chunks

    def pop_adjacent_chunks(self, chunk):
        """ Finds, removes and returns an iterable of chunks adjacent to chunk.

        For example: if our tree contains [0, 1], (2, 4) and we call pop_adjacent_chunks((1, 2]) then this function
        should return both nodes.

        """
        # NOTE: enumerating in POST_ORDER is a minor optimization guaranteeing that we will be popping leaf nodes first
        # which might lead to less reshuffling of the tree nodes.

        nodes_to_pop = [
            node
            for node
            in self.sorted_binary_tree.enumerate(order=SortedBinaryTree.POST_ORDER)
            if node.payload.is_contiguous_with(chunk)
        ]

        adjacent_chunks = [self.sorted_binary_tree.pop_node(node).payload for node in nodes_to_pop]
        return sorted(adjacent_chunks, key=lambda chunk: chunk.min)

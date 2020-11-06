#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import random

from mlos.Spaces.Dimensions.SortedBinaryTree import SortedBinaryTree, Stack

NUM_KEYS = 10000
RANGE = 100 * NUM_KEYS

class StackTest():

    def test_stack(self):
        stack = Stack()
        for i in range(100):
            stack.push(i)

        while not stack.is_empty:
            stack.pop()

        try:
            stack.pop()
            assert False
        except:
            assert True


class SortedBinaryTreeTest():

    def setUp(self):
        self.random_sorted_binary_tree = SortedBinaryTree()
        self.inserted_values = set()
        random.seed(1)
        for _ in range(NUM_KEYS):
            key = random.randint(0, RANGE)
            while key in self.inserted_values:
                key = random.randint(0, RANGE)
            self.random_sorted_binary_tree.add(key)
            self.inserted_values.add(key)

    def test_insert_and_contains(self):
        sorted_binary_tree = SortedBinaryTree()
        already_inserted = set()

        random.seed(1)
        for _ in range(1000):
            key = random.randint(0, 10000)
            while key in already_inserted:
                key = random.randint(0, 10000)
            sorted_binary_tree.add(key)
            assert sorted_binary_tree.contains(key)
            already_inserted.add(key)

        for key in already_inserted:
            assert sorted_binary_tree.contains(key)

    def test_traversal(self):
        previous_node = None
        for node in self.random_sorted_binary_tree.enumerate():
            if previous_node is not None:
                assert node.key >= previous_node.key
            previous_node = node

    def test_pop(self):
        sorted_binary_tree = SortedBinaryTree()
        sorted_binary_tree.add(key=1, payload='one')
        assert sorted_binary_tree.contains(1)
        assert sorted_binary_tree.pop(1) == 'one'
        assert not sorted_binary_tree.contains(1)

        keys = [i for i in range(10)]
        keys = sorted(keys, key=lambda x: random.random())

        for key in keys:
            sorted_binary_tree.add(key=key, payload=str(key))

        for key in keys:
            assert sorted_binary_tree.contains(key)

        for key in keys:
            payload = sorted_binary_tree.pop(key)
            sorted_binary_tree.assert_invariants()
            assert payload == str(key)

        for key in keys:
            assert not sorted_binary_tree.contains(key)

    def test_sanity(self):
        """ This test will exercise all functions of the tree by: inserting, looking up, removing keys.

        We will retain auxillary (and less efficient) data structures to ensure correctness.
        """

        INSERT_NEW = 0
        INSERT_EXISTING = 1
        LOOKUP_EXISTING = 2
        LOOKUP_NONEXISTENT = 4
        POP_EXISTING = 8
        POP_NONEXISTENT = 16

        OPERATIONS = [
            INSERT_NEW,
            INSERT_NEW,
            INSERT_NEW,
            INSERT_NEW,
            INSERT_NEW,
            INSERT_EXISTING,
            LOOKUP_EXISTING,
            LOOKUP_NONEXISTENT,
            POP_EXISTING,
            POP_NONEXISTENT,
        ]

        random.seed(2)
        num_iterations = 1000
        key_range = 100 * num_iterations
        sorted_binary_tree = SortedBinaryTree()
        inserted = set()
        removed = set()

        for i in range(num_iterations):
            # Each case will need one of the below
            existing_key = random.choice(list(inserted)) if inserted else None
            new_key = random.randint(0, key_range)
            while new_key in inserted:
                new_key = random.randint(0, key_range)

            OPERATION_TYPE = random.choice(OPERATIONS)
            while existing_key is None and OPERATION_TYPE in (INSERT_EXISTING, LOOKUP_EXISTING, POP_EXISTING):
                OPERATION_TYPE = random.choice(OPERATIONS)

            if OPERATION_TYPE == INSERT_NEW:
                sorted_binary_tree.add(new_key, str(new_key))
                inserted.add(new_key)
                if new_key in removed:
                    # If we re-inserted a new key, let's make sure to account for it.
                    removed.remove(new_key)
            elif OPERATION_TYPE == INSERT_EXISTING:
                try:
                    sorted_binary_tree.add(existing_key)
                    assert False
                except:
                    assert True

            elif OPERATION_TYPE == LOOKUP_EXISTING:
                assert sorted_binary_tree.contains(existing_key)
                assert sorted_binary_tree.get(existing_key) == str(existing_key)
                continue # No need to check invariants for read-only operations

            elif OPERATION_TYPE == LOOKUP_NONEXISTENT:
                assert not sorted_binary_tree.contains(new_key)
                try:
                    sorted_binary_tree.get(new_key)
                    assert False
                except:
                    assert True

            elif OPERATION_TYPE == POP_EXISTING:
                assert sorted_binary_tree.contains(existing_key)
                assert sorted_binary_tree.pop(existing_key) == str(existing_key)
                assert not sorted_binary_tree.contains(existing_key)
                inserted.remove(existing_key)
                removed.add(existing_key)

            elif OPERATION_TYPE == POP_NONEXISTENT:
                assert not sorted_binary_tree.contains(new_key)
                try:
                    sorted_binary_tree.get(new_key)
                    assert False
                except:
                    assert True

            else:
                assert False

            # let's validate invariants
            ## let's make sure that all keys are present
            for key in inserted:
                assert sorted_binary_tree.contains(key)

            ## let's make sure that all removed keys are not present
            for key in removed:
                assert not sorted_binary_tree.contains(key)

            ## let's make sure that the ordering is maintained
            if not sorted_binary_tree.is_empty():
                for set_key, tree_node in zip(sorted(inserted), sorted_binary_tree.enumerate()):
                    assert set_key == tree_node.key

    def test_stack_overflow(self):
        """ Inserts 10000 consecutive nodes which should cause stack overflow in the recursive implementation.

        """
        sorted_binary_tree = SortedBinaryTree()
        for key in range(5000, 10000):
            assert not sorted_binary_tree.contains(key)
            sorted_binary_tree.add(key=key, payload=str(key))

        for key in range(5000):
            assert not sorted_binary_tree.contains(key)
            sorted_binary_tree.add(key=key, payload=str(key))

        for expected_key, node in zip(range(10000), sorted_binary_tree.enumerate()):
            assert expected_key == node.key

        for key in range(5000, 10000):
            sorted_binary_tree.get(key)
            sorted_binary_tree.pop(key)
        assert True

    def test_binary_tree_enumeration(self):
        sorted_binary_tree = SortedBinaryTree()
        for key in [100, 50, 200, 25, 75, 150, 250]:
            sorted_binary_tree.add(key, str(key))

        pre_order_keys = [100, 50, 25, 75, 200, 150, 250]
        in_order_keys = [25, 50, 75, 100, 150, 200, 250]
        post_order_keys = [25, 75, 50, 150, 250, 200, 100]

        for expected_key, node in zip(pre_order_keys, sorted_binary_tree.enumerate(order=sorted_binary_tree.PRE_ORDER)):
            assert expected_key == node.key

        for expected_key, node in zip(in_order_keys, sorted_binary_tree.enumerate(order=sorted_binary_tree.IN_ORDER)):
            assert expected_key == node.key

        for expected_key, node in zip(post_order_keys, sorted_binary_tree.enumerate(order=sorted_binary_tree.POST_ORDER)):
            assert expected_key == node.key

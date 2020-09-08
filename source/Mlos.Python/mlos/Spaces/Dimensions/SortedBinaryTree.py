#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
class Stack:
    def __init__(self):
        self._stack = []

    @property
    def is_empty(self):
        return len(self._stack) == 0

    def push(self, element):
        self._stack.append(element)

    def pop(self):
        assert not self.is_empty
        return self._stack.pop(-1)

class StackedNode:
    """ Wraps a Node and its enumeration state to allow non-recursive enumeration.

    In order to support pre-order, in-order, and post-order enumeration,
    when we store a Node object on the stack (for Depth First Traversal)
    we need to keep track of how many times we have touched the Node.

    The whole idea is moving the search state from function-call stack to our
    explicitly built stack (both for perf and for stack-overflow protection).

    Examining how the function-stack maintains state we see that:
    * when a node is first seen, we build a stack frame for it
    * instruction pointer effectively keeps track of how many times the node has been
      touched since placed on the stack:
      * if zero times and we are traversing in PRE-ORDER we just need to push its children
        and can pop the node immediately
      * if traversing IN-ORDER we push right, node (with touched=1), left and whenever
        we pop a node with touched == 1, we yield it
      * if traversing in POST-ORDER we push node (with touched = 1), right, left and similarily
        yield a node only when it has been previously touched

    """
    def __init__(self, node):
        self.node = node
        self.touched = False

class Node:
    """ Models a node in a binary tree.

    To be able to support all binary tree operations efficiently, we need to keep track of:
    parent
    left child
    right child
    payload
    """
    PRE_ORDER = 0
    IN_ORDER = 1
    POST_ORDER = 2

    def __init__(self, key, payload, parent=None):
        self.parent = parent
        self.left = None
        self.right = None
        self.key = key
        self.payload = payload

    def __repr__(self):
        return f"Key: {self.key} Payload: {self.payload}"

    def has_left_child(self):
        return self.left is not None

    def has_right_child(self):
        return self.right is not None

    def has_both_children(self):
        return self.left is not None and self.right is not None

    def has_any_child(self):
        return self.left is not None or self.right is not None

    def is_root(self):
        return self.parent is None

    def is_left_child(self):
        if self.parent is None:
            return False
        if self.parent.left is None:
            return False
        if self.parent.left.key != self.key:
            return False
        return True

    def is_right_child(self):
        if self.parent is None:
            return False
        if self.parent.right is None:
            return False
        if self.parent.right.key != self.key:
            return False
        return True

    def swap_parent(self, new_parent):
        if self.is_left_child():
            assert self.key < new_parent.key
            self.parent.left = None
            new_parent.left = self
        else:
            assert self.key > new_parent.key
            self.parent.right = None
            new_parent.right = self
        self.parent = new_parent


class SortedBinaryTree:
    """ A data structure to keep payloads sorted.

    For each node N in the tree the following invariant holds between crud operations:
    1. Everything in N's left subtree has a payload smaller than N's.
    2. Everything in N's right subtree has a payload larger than N's.

    It basically has to support set operations:
    1. contains(payload)
    2. add(payload)
    3. pop(payload)

    Since we want to use it to organize intervals (that have a min and a max value), we need to be able to pop
    all intersecting intervals, perform a join, and then push the result back into the tree. We can keep the
    SortedBinaryTree generic by not supporting this in an efficient way, but then define a SortedIntervalBinaryTree
    to implement the Interval specific methods. This helps reusability as well as testability.

    Note: an attempt to add a key that already exists in the tree has to be handled. Our options to handle this case
    include:
        1. Fail with an exception - pretty good, but can be obnoxious to use.
        2. Fail with a return value - a little worse, because we rely on the caller to check the return value
        3. Replace the existing key - this would be in line with dict and set APIs, but if the caller is not expecting
           this behavior, they will have subtle and annoying bugs.
        4. Fail silently - no bueno.

    So let's go with the first option - an insert of an existing key fails with an exception.
    """

    PRE_ORDER = 0
    IN_ORDER = 1
    POST_ORDER = 2

    def __init__(self, root=None):
        self.root = root

    def __repr__(self):
        all_keys = [node.key for node in self.enumerate()]
        return str(all_keys)

    def enumerate(self, order=None):
        if order is None:
            order = self.IN_ORDER
        assert order in (self.PRE_ORDER, self.IN_ORDER, self.POST_ORDER)

        stack = Stack()
        if not self.is_empty():
            stack.push(StackedNode(self.root))

        while not stack.is_empty:
            current_node = stack.pop()

            if current_node.touched:
                yield current_node.node
                continue

            if order == self.POST_ORDER:
                current_node.touched = True
                stack.push(current_node)

            if current_node.node.has_right_child():
                stack.push(StackedNode(current_node.node.right))

            if order == self.IN_ORDER:
                current_node.touched = True
                stack.push(current_node)

            if current_node.node.has_left_child():
                stack.push(StackedNode(current_node.node.left))

            if order == self.PRE_ORDER:
                yield current_node.node


    def assert_invariants(self):
        if self.is_empty():
            return
        for node in self.enumerate():
            self.assert_node_invariants(node)

    @staticmethod
    def assert_node_invariants(node):
        if node.has_left_child():
            assert node.key > node.left.key
        if node.has_right_child():
            assert node.key < node.right.key

        assert (node.is_left_child() != node.is_right_child()) or node.is_root()
        if node.is_left_child():
            assert node.key < node.parent.key
            assert node.parent.left == node

        if node.is_right_child():
            assert node.key > node.parent.key
            assert node.parent.right == node

    def is_empty(self):
        return self.root is None

    def add(self, key, payload=None):
        if self.is_empty():
            self.root = Node(key=key, payload=payload)
            return

        current_parent = self.root
        while True:
            if current_parent.key == key:
                raise ValueError(f"Attempting to insert duplicate key: {key}")
            if current_parent.key > key:
                if current_parent.has_left_child():
                    current_parent = current_parent.left
                    continue
                current_parent.left = Node(key=key, payload=payload)
                current_parent.left.parent = current_parent
                return
            if current_parent.key < key:
                if current_parent.has_right_child():
                    current_parent = current_parent.right
                    continue
                current_parent.right = Node(key=key, payload=payload)
                current_parent.right.parent = current_parent
                return


    def get(self, key):
        current_node = self.root
        while current_node is not None:
            if key == current_node.key:
                return current_node.payload
            if key > current_node.key:
                current_node = current_node.right
            else:
                current_node = current_node.left
        raise KeyError(f"Attempting to retrieve a non-existing key: {key}")

    def contains(self, key):
        try:
            self.get(key)
            return True
        except KeyError:
            return False

    def pop(self, key):
        current_node = self.root
        while current_node is not None:
            if current_node.key > key:
                current_node = current_node.left
            elif current_node.key < key:
                current_node = current_node.right
            else: # current_node.key == key
                popped_node = self.pop_node(current_node)
                return popped_node.payload
        raise KeyError(f"Attempting to retrieve a non-existent key: {key}")

    def pop_node(self, node):
        if not node.has_any_child():
            if node.is_root():
                self.root = None
            elif node.is_left_child():
                node.parent.left = None
            else:
                node.parent.right = None
            node.parent = None
            return node

        # there is at least one child

        if node.has_both_children():
            # TODO: select the larger child to keep stuff balanced
            # NOTE: successor could be node's left child itself
            successor = self.pop_largest(node.left)

            if node.is_root():
                self.root = successor
            elif node.is_left_child():
                node.parent.left = successor
            else:
                node.parent.right = successor

            if node.has_left_child():
                node.left.swap_parent(new_parent=successor)
            if node.has_right_child():
                node.right.swap_parent(new_parent=successor)
            successor.parent = node.parent
            node.parent = None
            return node

        if node.has_left_child():
            if node.is_root():
                self.root = node.left
            elif node.is_left_child():
                node.parent.left = node.left
            else:
                node.parent.right = node.left

            # we only need to move it up a little
            node.left.parent = node.parent
            node.left = None
            node.parent = None
            return node

        if node.is_root():
            self.root = node.right
        elif node.is_left_child():
            node.parent.left = node.right
        else:
            node.parent.right = node.right
        node.right.parent = node.parent
        node.right = None
        node.parent = None
        return node

    def pop_largest(self, node):
        current_node = node
        while current_node.has_right_child():
            current_node = current_node.right
        return self.pop_node(current_node)

    def pop_smallest(self, node):
        current_node = node
        while current_node.has_left_child():
            current_node = current_node.left
        return self.pop_node(current_node)

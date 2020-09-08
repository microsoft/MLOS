#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
class LinkedList:
    def __init__(self):
        self.head = None
        self.tail = None

    def __iter__(self):
        return self.enumerate()

    def __repr__(self):
        return f"[{', '.join(str(node.cache_entry.key) for node in self)}]"

    def __len__(self):
        return len([element for element in self])

    def enumerate(self, reverse=False):
        current_node = self.head if not reverse else self.tail

        while current_node is not None:
            yield current_node
            current_node = current_node.next if not reverse else current_node.previous

    def move_to_head(self, node):

        node = self.remove_node(node)
        self.insert_at_head(node)

    def remove_node(self, node):

        if self.head == node:
            self.head = node.next
        elif node.previous is not None:
            node.previous.next = node.next
        else:
            assert False

        if self.tail == node:
            self.tail = node.previous
        elif node.next is not None:
            node.next.previous = node.previous
        else:
            assert False

        node.next = None
        node.previous = None
        return node

    def insert_at_head(self, node):
        assert node.previous is None
        node.next = self.head

        if node.next is None:
            self.tail = node

        if self.head is not None:
            self.head.previous = node

        self.head = node

    def remove_at_tail(self):
        node = self.tail
        if node is None:
            return node
        return self.remove_node(node)

    def remove_at_head(self):
        node = self.head
        if node is None:
            return node
        return self.remove_node(node)


class LinkedListNode:
    def __init__(self, cache_entry, previous=None, next=None):  # pylint: disable=redefined-builtin
        self.cache_entry = cache_entry
        self.previous = previous
        self.next = next

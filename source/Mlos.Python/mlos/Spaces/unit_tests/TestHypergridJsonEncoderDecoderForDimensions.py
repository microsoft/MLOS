#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import json
import unittest

from mlos.Spaces import EmptyDimension, ContinuousDimension

from mlos.Spaces.HypergridsJsonEncoderDecoder import HypergridJsonDecoder
from mlos.Spaces.HypergridsJsonEncoderDecoder import HypergridJsonEncoder


class TestHypergridJsonEncoderDecoderForDimensions(unittest.TestCase):
    """ Tests JSON encoding and decoding for hypergrids and dimensions.

    """

    def test_empty_dimension(self):
        empty_dimension = EmptyDimension(name="empty", type=ContinuousDimension)
        serialized = json.dumps(empty_dimension, cls=HypergridJsonEncoder)
        deserialized_dict = json.loads(serialized)
        deserialized_empty_dimension = json.loads(serialized, cls=HypergridJsonDecoder)

        self.assertTrue(deserialized_dict["ObjectType"] == "EmptyDimension")
        self.assertTrue(deserialized_dict["Type"] == "ContinuousDimension")
        self.assertTrue(deserialized_dict["Name"] == "empty")

        self.assertTrue(empty_dimension in deserialized_empty_dimension)
        self.assertTrue(deserialized_empty_dimension in empty_dimension)

    def test_composite_dimension(self):
        original_A = ContinuousDimension(name='x', min=0, max=1)
        original_B = ContinuousDimension(name='x', min=2, max=3)
        original_C = ContinuousDimension(name='x', min=2.5, max=3.5)
        original_D = original_A.union(original_B) - original_C
        original_E = original_B - original_C
        original_F = original_A.union(original_E)

        serialized_A = json.dumps(original_A, cls=HypergridJsonEncoder, indent=2)
        serialized_B = json.dumps(original_B, cls=HypergridJsonEncoder, indent=2)
        serialized_C = json.dumps(original_C, cls=HypergridJsonEncoder, indent=2)
        serialized_D = json.dumps(original_D, cls=HypergridJsonEncoder, indent=2)
        serialized_E = json.dumps(original_E, cls=HypergridJsonEncoder, indent=2)
        serialized_F = json.dumps(original_F, cls=HypergridJsonEncoder, indent=2)

        A = json.loads(serialized_A, cls=HypergridJsonDecoder)
        B = json.loads(serialized_B, cls=HypergridJsonDecoder)
        C = json.loads(serialized_C, cls=HypergridJsonDecoder)
        D = json.loads(serialized_D, cls=HypergridJsonDecoder)
        E = json.loads(serialized_E, cls=HypergridJsonDecoder)
        F = json.loads(serialized_F, cls=HypergridJsonDecoder)

        self.assertTrue(A in original_A)
        self.assertTrue(B in original_B)
        self.assertTrue(C in original_C)
        self.assertTrue(D in original_D)
        self.assertTrue(E in original_E)
        self.assertTrue(F in original_F)

        self.assertTrue(original_A in A)
        self.assertTrue(original_B in B)
        self.assertTrue(original_C in C)
        self.assertTrue(original_D in D)
        self.assertTrue(original_E in E)
        self.assertTrue(original_F in F)

        self.assertTrue(0.5 in D)
        self.assertTrue(1.5 not in D)
        self.assertTrue(2.5 not in D)
        self.assertTrue(3.4 not in D)
        self.assertTrue(35 not in D)
        self.assertTrue(2 in E)
        self.assertTrue(2.5 not in E)
        self.assertTrue(0 in F and 1 in F and 1.5 not in F and 2 in F and 2.5 not in F)

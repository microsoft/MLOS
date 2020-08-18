#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import unittest

from mlos.Mlos.SDK import MlosObject

class TestMlosObject(unittest.TestCase):

    def test_reconfiguration_lock(self):
        mlos_object = MlosObject(int, int)

        self.assertFalse(mlos_object._reconfiguration_lock._is_owned())
        with mlos_object.reconfiguration_lock():
            self.assertTrue(mlos_object._reconfiguration_lock._is_owned())
        self.assertFalse(mlos_object._reconfiguration_lock._is_owned())

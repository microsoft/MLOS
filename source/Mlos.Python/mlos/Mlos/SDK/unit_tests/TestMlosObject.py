#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#

from mlos.Mlos.SDK import MlosObject

class TestMlosObject:

    def test_reconfiguration_lock(self):
        mlos_object = MlosObject(int, int)

        assert not mlos_object._reconfiguration_lock._is_owned()
        with mlos_object.reconfiguration_lock():
            assert mlos_object._reconfiguration_lock._is_owned()
        assert not mlos_object._reconfiguration_lock._is_owned()

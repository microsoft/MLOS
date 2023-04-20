#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests to make sure we always produce a string representation
of a TunableGroup in canonical form.
"""

from mlos_bench.tunables.tunable_groups import TunableGroups


def test_tunable_groups_str(tunable_groups: TunableGroups) -> None:
    """
    Check if deep copy works for TunableGroups object.
    """
    tunables_other = TunableGroups({
        "kernel": {
            "cost": 1,
            "params": {
                "kernel_sched_migration_cost_ns": {
                    "description": "Cost of migrating the thread to another core",
                    "type": "int",
                    "default": -1,
                    "range": [-1, 500000],
                    "special": [-1]
                }
            }
        },
        "provision": {
            "cost": 1000,
            "params": {
                "vmSize": {
                    "description": "Azure VM size",
                    "type": "categorical",
                    "default": "Standard_B4ms",
                    "values": ["Standard_B2s", "Standard_B2ms", "Standard_B4ms"]
                }
            }
        },
        "boot": {
            "cost": 300,
            "params": {
                "rootfs": {
                    "description": "Root file system",
                    "type": "categorical",
                    "default": "xfs",
                    "values": ["xfs", "ext4", "ext2"]
                }
            }
        },
    })
    assert tunable_groups == tunables_other

#!/usr/bin/env python3
#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Python script to parse through JSON and create new config file.

This script will be run in the SCHEDULER. NEW_CFG will need to be copied over to the VM
(/etc/default/grub.d).
"""
import json

JSON_CONFIG_FILE = "config-boot-time.json"
NEW_CFG = "zz-mlos-boot-params.cfg"

with open(JSON_CONFIG_FILE, "r", encoding="UTF-8") as fh_json, open(
    NEW_CFG, "w", encoding="UTF-8"
) as fh_config:
    for key, val in json.load(fh_json).items():
        fh_config.write(
            'GRUB_CMDLINE_LINUX_DEFAULT="$' f'{{GRUB_CMDLINE_LINUX_DEFAULT}} {key}={val}"\n'
        )

#!/usr/bin/env python3
#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Python script to parse through JSON, store runtime parameter paths, and
create script to apply new runtime parameters in VM.
This script will be run in the scheduler.
Both PATHS_FILE and RUNTIME_PARAMS will need to copied to the VM.
"""
import json

JSON_CONFIG_FILE = "config-runtime.json"
RUNTIME_PARAMS = "runtime_params.tsv"
PATHS_FILE = "paths.txt"

# parse through JSON to create new params array & paths and tsv files
with open(JSON_CONFIG_FILE, 'r', encoding='UTF-8') as fh_json, \
     open(PATHS_FILE, 'wt', encoding='UTF-8') as fh_paths, \
     open(RUNTIME_PARAMS, 'wt', encoding='UTF-8') as fh_tsv:
    for key, val in json.load(fh_json).items():
        fh_paths.write(f"{key}\n")
        fh_tsv.write(f"{key}\t{val}\n")

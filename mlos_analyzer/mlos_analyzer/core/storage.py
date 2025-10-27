#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from mlos_bench.storage import from_config

try:
    storage = from_config(config="storage/sqlite.jsonc")  # PLACEHOLDER
except Exception as e:
    raise Exception(f"Error loading storage configuration: {e}")

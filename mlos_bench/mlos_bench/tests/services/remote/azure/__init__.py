#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Tests helpers for mlos_bench.services.remote.azure."""
import json
from io import BytesIO

import urllib3


def make_httplib_json_response(status: int, json_data: dict) -> urllib3.HTTPResponse:
    """Prepare a json response object for use with urllib3."""
    data = json.dumps(json_data).encode("utf-8")
    response = urllib3.HTTPResponse(
        status=status,
        body=BytesIO(data),
        preload_content=False,
    )
    return response

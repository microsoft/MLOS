#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Unit tests for get_git_info utility function.
"""
import os
import re

from mlos_bench.util import get_git_info


def test_get_git_info() -> None:
    """
    Check that we can retrieve git info about the current repository correctly.
    """
    (git_repo, git_commit) = get_git_info(os.path.dirname(__file__))
    assert "mlos" in git_repo.lower()
    assert re.match(r"[0-9a-f]{40}", git_commit) is not None

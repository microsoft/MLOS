#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for get_git_info utility function."""
import re

from mlos_bench.util import get_git_info


def test_get_git_info() -> None:
    """Check that we can retrieve git info about the current repository correctly."""
    (git_repo, git_commit, rel_path) = get_git_info(__file__)
    assert "mlos" in git_repo.lower()
    assert re.match(r"[0-9a-f]{40}", git_commit) is not None
    assert rel_path == "mlos_bench/mlos_bench/tests/util_git_test.py"

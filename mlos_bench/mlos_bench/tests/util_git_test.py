#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for get_git_info utility function."""
import os
import re
import tempfile
from subprocess import CalledProcessError

import pytest

from mlos_bench.util import get_git_info, get_git_root, path_join


def test_get_git_info() -> None:
    """Check that we can retrieve git info about the current repository correctly from a
    file.
    """
    (git_repo, git_commit, rel_path, abs_path) = get_git_info(__file__)
    assert "mlos" in git_repo.lower()
    assert re.match(r"[0-9a-f]{40}", git_commit) is not None
    assert rel_path == "mlos_bench/mlos_bench/tests/util_git_test.py"
    assert abs_path == path_join(__file__, abs_path=True)


def test_get_git_info_dir() -> None:
    """Check that we can retrieve git info about the current repository correctly from a
    directory.
    """
    dirname = os.path.dirname(__file__)
    (git_repo, git_commit, rel_path, abs_path) = get_git_info(dirname)
    assert "mlos" in git_repo.lower()
    assert re.match(r"[0-9a-f]{40}", git_commit) is not None
    assert rel_path == "mlos_bench/mlos_bench/tests"
    assert abs_path == path_join(dirname, abs_path=True)


def test_non_git_dir() -> None:
    """Check that we can handle a non-git directory."""
    with tempfile.TemporaryDirectory() as non_git_dir:
        with pytest.raises(CalledProcessError):
            # This should raise an error because the directory is not a git repository.
            get_git_root(non_git_dir)

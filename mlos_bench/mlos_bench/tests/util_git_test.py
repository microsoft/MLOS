#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Unit tests for get_git_info utility function."""
import os
import re
import tempfile
from pathlib import Path
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


def test_non_upstream_git() -> None:
    """Check that we can handle a git directory without an upstream."""
    with tempfile.TemporaryDirectory() as non_upstream_git_dir:
        non_upstream_git_dir = path_join(non_upstream_git_dir, abs_path=True)
        # Initialize a new git repository.
        os.system(f"git init {non_upstream_git_dir} -b main")
        os.system(f"git -C {non_upstream_git_dir} config --local user.email 'pytest@example.com'")
        os.system(f"git -C {non_upstream_git_dir} config --local user.name 'PyTest User'")
        Path(non_upstream_git_dir).joinpath("README.md").touch()
        os.system(f"git -C {non_upstream_git_dir} add README.md")
        os.system(f"git -C {non_upstream_git_dir} commit -m 'Initial commit'")
        # This should raise an error because the repository has no upstream.
        (git_repo, _git_commit, rel_path, abs_path) = get_git_info(non_upstream_git_dir)
        assert git_repo == f"file://{non_upstream_git_dir}"
        assert abs_path == non_upstream_git_dir
        assert rel_path == "."


@pytest.mark.skipif(
    os.environ.get("GITHUB_ACTIONS") != "true",
    reason="Not running in GitHub Actions CI.",
)
def test_github_actions_git_info() -> None:
    """Test that get_git_info matches GitHub Actions environment variables if running in
    CI.
    """
    repo_env = os.environ.get("GITHUB_REPOSITORY")  # "owner/repo" format
    sha_env = os.environ.get("GITHUB_SHA")
    assert repo_env, "GITHUB_REPOSITORY not set in environment."
    assert sha_env, "GITHUB_SHA not set in environment."
    git_repo, git_commit, _rel_path, _abs_path = get_git_info(__file__)
    assert git_repo.endswith(repo_env), f"git_repo '{git_repo}' does not end with '{repo_env}'"
    assert (
        git_commit == sha_env
    ), f"git_commit '{git_commit}' does not match GITHUB_SHA '{sha_env}'"

#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""Various helper functions for mlos_bench."""

# NOTE: This has to be placed in the top-level mlos_bench package to avoid circular imports.

import importlib
import json
import logging
import os
import subprocess
from collections.abc import Callable, Iterable, Mapping
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal, TypeVar, Union

import pandas
import pytz

_LOG = logging.getLogger(__name__)

if TYPE_CHECKING:
    from mlos_bench.environments.base_environment import Environment
    from mlos_bench.optimizers.base_optimizer import Optimizer
    from mlos_bench.schedulers.base_scheduler import Scheduler
    from mlos_bench.services.base_service import Service
    from mlos_bench.storage.base_storage import Storage

BaseTypeVar = TypeVar("BaseTypeVar", "Environment", "Optimizer", "Scheduler", "Service", "Storage")
"""BaseTypeVar is a generic with a constraint of the main base classes (e.g.,
:py:class:`~mlos_bench.environments.base_environment.Environment`,
:py:class:`~mlos_bench.optimizers.base_optimizer.Optimizer`,
:py:class:`~mlos_bench.schedulers.base_scheduler.Scheduler`,
:py:class:`~mlos_bench.services.base_service.Service`,
:py:class:`~mlos_bench.storage.base_storage.Storage`, etc.).
"""

BaseTypes = Union[  # pylint: disable=consider-alternative-union-syntax
    "Environment", "Optimizer", "Scheduler", "Service", "Storage"
]
"""Similar to :py:data:`.BaseTypeVar`, BaseTypes is a Union of the main base classes."""


# Adjusted from https://github.com/python/cpython/blob/v3.11.10/Lib/distutils/util.py#L308
# See Also: https://github.com/microsoft/MLOS/issues/865
def strtobool(val: str) -> bool:
    """
    Convert a string representation of truth to true (1) or false (0).

    Parameters
    ----------
    val : str
        True values are 'y', 'yes', 't', 'true', 'on', and '1';
        False values are 'n', 'no', 'f', 'false', 'off', and '0'.

    Raises
    ------
    ValueError
        If 'val' is anything else.
    """
    val = val.lower()
    if val in {"y", "yes", "t", "true", "on", "1"}:
        return True
    elif val in {"n", "no", "f", "false", "off", "0"}:
        return False
    else:
        raise ValueError(f"Invalid Boolean value: '{val}'")


def preprocess_dynamic_configs(*, dest: dict, source: dict | None = None) -> dict:
    """
    Replaces all ``$name`` values in the destination config with the corresponding value
    from the source config.

    Parameters
    ----------
    dest : dict
        Destination config.
    source : dict | None
        Source config.

    Returns
    -------
    dest : dict
        A reference to the destination config after the preprocessing.
    """
    if source is None:
        source = {}
    for key, val in dest.items():
        if isinstance(val, str) and val.startswith("$") and val[1:] in source:
            dest[key] = source[val[1:]]
    return dest


def merge_parameters(
    *,
    dest: dict,
    source: dict | None = None,
    required_keys: Iterable[str] | None = None,
) -> dict:
    """
    Merge the source config dict into the destination config. Pick from the source
    configs *ONLY* the keys that are already present in the destination config.

    Parameters
    ----------
    dest : dict
        Destination config.
    source : dict | None
        Source config.
    required_keys : Optional[Iterable[str]]
        An optional list of keys that must be present in the destination config.

    Returns
    -------
    dest : dict
        A reference to the destination config after the merge.
    """
    if source is None:
        source = {}

    for key in set(dest).intersection(source):
        dest[key] = source[key]

    for key in required_keys or []:
        if key in dest:
            continue
        if key in source:
            dest[key] = source[key]
        else:
            raise ValueError("Missing required parameter: " + key)

    return dest


def path_join(*args: str, abs_path: bool = False) -> str:
    """
    Joins the path components and normalizes the path.

    Parameters
    ----------
    args : str
        Path components.

    abs_path : bool
        If True, the path is converted to be absolute.

    Returns
    -------
    str
        Joined path.
    """
    path = os.path.join(*args)
    if abs_path:
        path = os.path.realpath(path)
    return os.path.normpath(path).replace("\\", "/")


def prepare_class_load(
    config: dict,
    global_config: dict[str, Any] | None = None,
) -> tuple[str, dict[str, Any]]:
    """
    Extract the class instantiation parameters from the configuration.

    Parameters
    ----------
    config : dict
        Configuration of the optimizer.
    global_config : dict
        Global configuration parameters (optional).

    Returns
    -------
    (class_name, class_config) : (str, dict)
        Name of the class to instantiate and its configuration.
    """
    class_name = config["class"]
    class_config = config.setdefault("config", {})

    merge_parameters(dest=class_config, source=global_config)

    if _LOG.isEnabledFor(logging.DEBUG):
        _LOG.debug(
            "Instantiating: %s with config:\n%s", class_name, json.dumps(class_config, indent=2)
        )

    return (class_name, class_config)


def get_class_from_name(class_name: str) -> type:
    """
    Gets the class from the fully qualified name.

    Parameters
    ----------
    class_name : str
        Fully qualified class name.

    Returns
    -------
    type
        Class object.
    """
    # We need to import mlos_bench to make the factory methods work.
    class_name_split = class_name.split(".")
    module_name = ".".join(class_name_split[:-1])
    class_id = class_name_split[-1]

    module = importlib.import_module(module_name)
    cls = getattr(module, class_id)
    assert isinstance(cls, type)
    return cls


# FIXME: Technically, this should return a type "class_name" derived from "base_class".
def instantiate_from_config(
    base_class: type[BaseTypeVar],
    class_name: str,
    *args: Any,
    **kwargs: Any,
) -> BaseTypeVar:
    """
    Factory method for a new class instantiated from config.

    Parameters
    ----------
    base_class : type
        Base type of the class to instantiate.
        Currently it's one of {Environment, Service, Optimizer}.
    class_name : str
        FQN of a Python class to instantiate, e.g.,
        "mlos_bench.environments.remote.HostEnv".
        Must be derived from the `base_class`.
    args : list
        Positional arguments to pass to the constructor.
    kwargs : dict
        Keyword arguments to pass to the constructor.

    Returns
    -------
    inst : Union[Environment, Service, Optimizer, Storage]
        An instance of the `class_name` class.
    """
    impl = get_class_from_name(class_name)
    _LOG.info("Instantiating: %s :: %s", class_name, impl)

    assert issubclass(impl, base_class)
    ret: BaseTypeVar = impl(*args, **kwargs)
    assert isinstance(ret, base_class)
    return ret


def check_required_params(config: Mapping[str, Any], required_params: Iterable[str]) -> None:
    """
    Check if all required parameters are present in the configuration. Raise ValueError
    if any of the parameters are missing.

    Parameters
    ----------
    config : dict
        Free-format dictionary with the configuration
        of the service or benchmarking environment.
    required_params : Iterable[str]
        A collection of identifiers of the parameters that must be present
        in the configuration.
    """
    missing_params = set(required_params).difference(config)
    if missing_params:
        raise ValueError(
            "The following parameters must be provided in the configuration"
            + f" or as command line arguments: {missing_params}"
        )


def get_git_root(path: str = __file__) -> str:
    """
    Get the root dir of the git repository.

    Parameters
    ----------
    path : Optional[str]
        Path to the file in git repository.

    Raises
    ------
    subprocess.CalledProcessError
        If the path is not a git repository or the command fails.

    Returns
    -------
    str
        The absolute path to the root directory of the git repository.
    """
    abspath = path_join(path, abs_path=True)
    if not os.path.exists(abspath) or not os.path.isdir(abspath):
        dirname = os.path.dirname(abspath)
    else:
        dirname = abspath
    git_root = subprocess.check_output(
        ["git", "-C", dirname, "rev-parse", "--show-toplevel"], text=True
    ).strip()
    return path_join(git_root, abs_path=True)


def get_git_remote_info(path: str, remote: str) -> str:
    """
    Gets the remote URL for the given remote name in the git repository.

    Parameters
    ----------
    path : str
        Path to the file in git repository.
    remote : str
        The name of the remote (e.g., "origin").

    Raises
    ------
    subprocess.CalledProcessError
        If the command fails or the remote does not exist.

    Returns
    -------
    str
        The URL of the remote repository.
    """
    return subprocess.check_output(
        ["git", "-C", path, "remote", "get-url", remote], text=True
    ).strip()


def get_git_repo_info(path: str) -> str:
    """
    Get the git repository URL for the given git repo.

    Tries to get the upstream branch URL, falling back to the "origin" remote
    if the upstream branch is not set or does not exist. If that also fails,
    it returns a file URL pointing to the local path.

    Parameters
    ----------
    path : str
        Path to the git repository.

    Raises
    ------
    subprocess.CalledProcessError
        If the command fails or the git repository does not exist.

    Returns
    -------
    str
        The upstream URL of the git repository.
    """
    # In case "origin" remote is not set, or this branch has a different
    # upstream, we should handle it gracefully.
    # (e.g., fallback to the first one we find?)
    path = path_join(path, abs_path=True)
    cmd = ["git", "-C", path, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "HEAD@{u}"]
    try:
        git_remote = subprocess.check_output(cmd, text=True).strip()
        git_remote = git_remote.split("/", 1)[0]
        git_repo = get_git_remote_info(path, git_remote)
    except subprocess.CalledProcessError:
        git_remote = "origin"
        _LOG.warning(
            "Failed to get the upstream branch for %s. Falling back to '%s' remote.",
            path,
            git_remote,
        )
        try:
            git_repo = get_git_remote_info(path, git_remote)
        except subprocess.CalledProcessError:
            git_repo = "file://" + path
            _LOG.warning(
                "Failed to get the upstream branch for %s. Falling back to '%s'.",
                path,
                git_repo,
            )
    return git_repo


def get_git_info(path: str = __file__) -> tuple[str, str, str, str]:
    """
    Get the git repository, commit hash, and local path of the given file.

    Parameters
    ----------
    path : str
        Path to the file in git repository.

    Raises
    ------
    subprocess.CalledProcessError
        If the path is not a git repository or the command fails.

    Returns
    -------
    (git_repo, git_commit, rel_path, abs_path) : tuple[str, str, str, str]
        Git repository URL, last commit hash, and relative file path and current
        absolute path.
    """
    abspath = path_join(path, abs_path=True)
    if os.path.exists(abspath) and os.path.isdir(abspath):
        dirname = abspath
    else:
        dirname = os.path.dirname(abspath)
    git_root = get_git_root(path=abspath)
    git_repo = get_git_repo_info(git_root)
    git_commit = subprocess.check_output(
        ["git", "-C", dirname, "rev-parse", "HEAD"], text=True
    ).strip()
    _LOG.debug("Current git branch for %s: %s %s", git_root, git_repo, git_commit)
    rel_path = os.path.relpath(abspath, os.path.abspath(git_root))
    # TODO: return the branch too?
    return (git_repo, git_commit, rel_path.replace("\\", "/"), abspath)


# TODO: Add support for checking out the branch locally.


# Note: to avoid circular imports, we don't specify TunableValue here.
def try_parse_val(val: str | None) -> int | float | str | None:
    """
    Try to parse the value as an int or float, otherwise return the string.

    This can help with config schema validation to make sure early on that
    the args we're expecting are the right type.

    Parameters
    ----------
    val : str
        The initial cmd line arg value.

    Returns
    -------
    TunableValue
        The parsed value.
    """
    if val is None:
        return val
    try:
        val_float = float(val)
        try:
            val_int = int(val)
            return val_int if val_int == val_float else val_float
        except (ValueError, OverflowError):
            return val_float
    except ValueError:
        return str(val)


NullableT = TypeVar("NullableT")
"""A generic type variable for :py:func:`nullable` return types."""


def nullable(func: Callable[..., NullableT], value: Any | None) -> NullableT | None:
    """
    Poor man's Maybe monad: apply the function to the value if it's not None.

    Parameters
    ----------
    func : Callable
        Function to apply to the value.
    value : Any | None
        Value to apply the function to.

    Returns
    -------
    value : NullableT | None
        The result of the function application or None if the value is None.

    Examples
    --------
    >>> nullable(int, "1")
    1
    >>> nullable(int, None)
    ...
    >>> nullable(str, 1)
    '1'
    """
    return None if value is None else func(value)


def utcify_timestamp(timestamp: datetime, *, origin: Literal["utc", "local"]) -> datetime:
    """
    Augment a timestamp with zoneinfo if missing and convert it to UTC.

    Parameters
    ----------
    timestamp : datetime.datetime
        A timestamp to convert to UTC.
        Note: The original datetime may or may not have tzinfo associated with it.

    origin : Literal["utc", "local"]
        Whether the source timestamp is considered to be in UTC or local time.
        In the case of loading data from storage, where we intentionally convert all
        timestamps to UTC, this can help us retrieve the original timezone when the
        storage backend doesn't explicitly store it.
        In the case of receiving data from a client or other source, this can help us
        convert the timestamp to UTC if it's not already.

    Returns
    -------
    datetime.datetime
        A datetime with zoneinfo in UTC.
    """
    if timestamp.tzinfo is not None or origin == "local":
        # A timestamp with no zoneinfo is interpretted as "local" time
        # (e.g., according to the TZ environment variable).
        # That could be UTC or some other timezone, but either way we convert it to
        # be explicitly UTC with zone info.
        return timestamp.astimezone(pytz.UTC)
    elif origin == "utc":
        # If the timestamp is already in UTC, we just add the zoneinfo without conversion.
        # Converting with astimezone() when the local time is *not* UTC would cause
        # a timestamp conversion which we don't want.
        return timestamp.replace(tzinfo=pytz.UTC)
    else:
        raise ValueError(f"Invalid origin: {origin}")


def utcify_nullable_timestamp(
    timestamp: datetime | None,
    *,
    origin: Literal["utc", "local"],
) -> datetime | None:
    """A nullable version of utcify_timestamp."""
    return utcify_timestamp(timestamp, origin=origin) if timestamp is not None else None


# All timestamps in the telemetry data must be greater than this date
# (a very rough approximation for the start of this feature).
_MIN_TS = datetime(2024, 1, 1, 0, 0, 0, tzinfo=pytz.UTC)


def datetime_parser(
    datetime_col: pandas.Series,
    *,
    origin: Literal["utc", "local"],
) -> pandas.Series:
    """
    Attempt to convert a pandas column to a datetime format.

    Parameters
    ----------
    datetime_col : pandas.Series
        The column to convert.

    origin : Literal["utc", "local"]
        Whether to interpret naive timestamps as originating from UTC or local time.

    Returns
    -------
    pandas.Series
        The converted datetime column.

    Raises
    ------
    ValueError
        On parse errors.
    """
    new_datetime_col = pandas.to_datetime(datetime_col, utc=False)
    # If timezone data is missing, assume the provided origin timezone.
    if new_datetime_col.dt.tz is None:
        if origin == "local":
            tzinfo = datetime.now().astimezone().tzinfo
        elif origin == "utc":
            tzinfo = pytz.UTC
        else:
            raise ValueError(f"Invalid timezone origin: {origin}")
        new_datetime_col = new_datetime_col.dt.tz_localize(tzinfo)
    assert new_datetime_col.dt.tz is not None
    # And convert it to UTC.
    new_datetime_col = new_datetime_col.dt.tz_convert("UTC")
    if new_datetime_col.isna().any():
        raise ValueError(f"Invalid date format in the data: {datetime_col}")
    if new_datetime_col.le(_MIN_TS).any():
        raise ValueError(f"Invalid date range in the data: {datetime_col}")
    return new_datetime_col


def sanitize_config(config: dict[str, Any]) -> dict[str, Any]:
    """
    Sanitize a configuration dictionary by obfuscating potentially sensitive keys.

    Parameters
    ----------
    config : dict
        Configuration dictionary to sanitize.

    Returns
    -------
    dict
        Sanitized configuration dictionary.
    """
    sanitize_keys = {"password", "secret", "token", "api_key"}

    def recursive_sanitize(conf: dict[str, Any]) -> dict[str, Any]:
        """Recursively sanitize a dictionary."""
        sanitized = {}
        for k, v in conf.items():
            if k in sanitize_keys:
                sanitized[k] = "[REDACTED]"
            elif isinstance(v, dict):
                sanitized[k] = recursive_sanitize(v)  # type: ignore[assignment]
            else:
                sanitized[k] = v
        return sanitized

    return recursive_sanitize(config)

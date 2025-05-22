"""
Unit tests for base scheduler internals.
"""

import pytest

from mlos_bench.schedulers import Scheduler, SyncScheduler
from mlos_bench.tests.schedulers import MockScheduler


# TODO:
# Develop unit tests for schedulers.
# e.g., using MockScheduler it should validate that
# - the base scheduler can be used to run a trial
# - the base scheduler registers the values it receives from the mock_trial_data correctly
# - the base scheduler can be used to run multiple trials
# - the base scheduler does book keeping correctly

# Actually, maybe what I really want is a MockTrialRunner that can be used to
# return dummy trial results after some predictable period for use in both
# parallel and synchronous schedulers.

# No, in fact we can do that all with MockEnv and a small extension there.

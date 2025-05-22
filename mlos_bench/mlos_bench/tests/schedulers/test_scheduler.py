"""
Unit tests for base scheduler internals.

Notes
-----
Some prompts to help write the tests:

Develop unit tests for `Scheduler` class.
- use `@pytest.mark.parametrize` to run the same test with different Scheduler classes (e.g. `SyncScheduler`, `ParallelScheduler`, etc.)
- use `MockEnv` with `mock_trial_data` as a `pytest.fixture` to run the tests
  - needs a jsonc file or string that the `TrialRunner.create_from_json` method can use to create the Env multiple times

Check that:
1. the targeted scheduler can be used to run a trial
   - check that results are stored in the storage backend correctly
     - use the `sqlite_storage` fixture from `mlos_bench.tests.storage.sql.fixtures` for that
   - check that the `_ran_trials` attribute is updated correctly after a run_scheduler call
2. the base scheduler `bulk_registers` the values it receives from the mock_trial_data correctly
     - use `mock` to patch the `bulk_register` method in the `Scheduler` class's `optimizer` attribute and check the call arguments
3. the base scheduler does book keeping correctly
   - use `mock` to patch the `add_new_optimizer_suggestions` method in the `Scheduler` class and check the `_last_trial_id`
"""

import pytest
import unittest.mock

from mlos_bench.schedulers import Scheduler, SyncScheduler

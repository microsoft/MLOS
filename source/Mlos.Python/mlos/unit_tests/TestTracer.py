#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import json
import time
import unittest

from mlos.Tracer import Tracer, trace, add_trace_event
import mlos.global_values as global_values

class TestTracer(unittest.TestCase):
    """ Validates the global singleton Tracer can be properly initialized and used.

    """

    def test_tracer(self):
        global_values.declare_singletons()
        global_values.tracer = Tracer(actor_id='1', thread_id='0')

        try:
            fib_number = self.fibonacci(n=3)
        except:
            pass
        trace_events = global_values.tracer.trace_events
        reformatted_events = Tracer.reformat_events(trace_events)
        self.assertTrue(len(trace_events) > 0)
        print(json.dumps(reformatted_events, indent=2))

    @trace()
    def fibonacci(self, n):
        time.sleep(0.1)
        assert n > 0, "n must be larger than 0"
        return 1 if n <= 1 else self.fibonacci(n=n-1) + self.fibonacci(n=n-2)  # Note: this is meant to throw

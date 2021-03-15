#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#

class RandomNearIncumbentTracer:
    """Traces the execution of the RandomNearIncumbentOptimizer.

    The goal here is to capture data on every stage of the optimization:
        1. What were the original incumbents?
        2. What were the neighbors at a given iteration?
        3. What are the new incumbents after a given iteration

    This tracer subscribes to the events produced by the Tracer, and thus gets access to all the data we need.

    """

    def __init__(self):
        self.ordered_events = []

    def add_trace_event(self, name, phase, timestamp_ns, category, actor_id, thread_id, arguments):
        if name.startswith("RandomNearIncumbentOptimizer"):
            print(name, phase)
            self.ordered_events.append(dict(
                name=name,
                phase=phase,
                arguments=arguments
            ))

    def clear_events(self):
        self.ordered_events = []

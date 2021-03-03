#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from contextlib import contextmanager
from functools import wraps
import json
import os
import time
from threading import current_thread
from typing import Dict

import pandas as pd

from mlos import global_values


# This is defined outside of the class, because the first parameter has to be
# the wrapped function, but inside the class it would have been treated as self.
def trace():
    def tracing_decorator(wrapped_function):
        @wraps(wrapped_function)
        def wrapper(*args, **kwargs):
            tracer = getattr(global_values, 'tracer', None)
            if tracer is not None:
                start_timestamp_ns = int(time.time() * 1000000)
                thread_id = current_thread().ident
                tracer.add_trace_event(name=wrapped_function.__qualname__, phase='B', timestamp_ns=start_timestamp_ns, thread_id=thread_id, arguments=kwargs)
                try:
                    result = wrapped_function(*args, **kwargs)
                    end_timestamp_ns = int(time.time() * 1000000)
                    while end_timestamp_ns <= start_timestamp_ns:
                        end_timestamp_ns += 100
                    arguments = None
                    if result is not None and isinstance(result, (str, int, float, bool)):
                        arguments = {'result': result}
                    tracer.add_trace_event(
                        name=wrapped_function.__qualname__,
                        phase='E',
                        timestamp_ns=end_timestamp_ns,
                        thread_id=thread_id,
                        arguments=arguments
                    )
                except Exception as e:
                    arguments = {'exception': str(e)}
                    end_timestamp_ns = int(time.time() * 1000000)
                    while end_timestamp_ns <= start_timestamp_ns:
                        end_timestamp_ns += 100
                    tracer.add_trace_event(
                        name=wrapped_function.__qualname__,
                        phase='E',
                        timestamp_ns=end_timestamp_ns,
                        thread_id=thread_id,
                        arguments=arguments
                    )
                    raise e

            else:
                result = wrapped_function(*args, **kwargs)

            return result

        return wrapper
    return tracing_decorator


def add_trace_event(name, phase, category='', timestamp_ns=None, actor_id=None, thread_id=None, arguments=None):
    tracer = getattr(global_values, 'tracer', None)
    if tracer is not None:
        tracer.add_trace_event(
            name,
            phase,
            timestamp_ns=timestamp_ns,
            category=category,
            actor_id=actor_id,
            thread_id=thread_id,
            arguments=arguments
        )


@contextmanager
def traced(scope_name):
    start_timestamp_ns = int(time.time() * 1000000)
    thread_id = current_thread().ident
    add_trace_event(name=scope_name, phase="B", timestamp_ns=start_timestamp_ns, thread_id=thread_id)

    yield

    end_timestamp_ns = int(time.time() * 1000000)
    while end_timestamp_ns <= start_timestamp_ns:
        end_timestamp_ns += 100
    add_trace_event(name=scope_name, phase="E", timestamp_ns=end_timestamp_ns, thread_id=thread_id)


class Tracer:
    """ Collects a trace of events to be displayed by chrome://tracing.

    """

    def __init__(self, actor_id=None, thread_id=None):
        pid = os.getpid()

        if actor_id is None:
            actor_id = pid
        else:
            actor_id = f"{actor_id}.{pid}"
        self.actor_id = actor_id

        if thread_id is None:
            thread_id = current_thread().ident
        self.thread_id = thread_id
        self._trace_events = []

    @property
    def trace_events(self):
        return self._trace_events

    @trace_events.setter
    def trace_events(self, value):
        self._trace_events = value

    @staticmethod
    def reformat_events(events):
        key_mappings = {
            "name": "name",
            "timestamp_ns": "ts",
            "category": "cat",
            "actor_id": "pid",
            "thread_id": "tid",
            "args": "args",
            "phase": "ph"
        }
        reformatted_trace_events = []
        for event in events:
            reformatted_event = {}
            for key, value in event.items():
                reformatted_event[key_mappings[key]] = value if key != "args" else json.loads(value)
            reformatted_trace_events.append(reformatted_event)

        return reformatted_trace_events

    def dump_trace_to_string(self):
        reformatted_trace_events = self.reformat_events(self._trace_events)
        return json.dumps(reformatted_trace_events, indent=2)

    def dump_trace_to_file(self, output_file_path):
        reformatted_trace_events = self.reformat_events(self._trace_events)
        with open(output_file_path, 'w') as out_file:
            out_file.write(json.dumps(reformatted_trace_events, indent=2))

    def clear_events(self):
        self._trace_events = []

    def add_trace_event(self, name, phase, timestamp_ns=None, category='', actor_id=None, thread_id=None, arguments=None):
        assert phase in {'B', 'E'}, f"Unrecognized category name: {category}."
        if timestamp_ns is None:
            timestamp_ns = int(time.time() * 1000000)
        trace_event = dict()

        # The +/- 1 should help with proper nesting.
        if phase == 'B':
            trace_event["timestamp_ns"] = timestamp_ns + 1
        else:
            trace_event["timestamp_ns"] = timestamp_ns - 1

        trace_event["name"] = name
        trace_event["phase"] = phase
        trace_event["category"] = category
        trace_event["actor_id"] = self.actor_id if actor_id is None else actor_id
        trace_event["thread_id"] = self.thread_id if thread_id is None else thread_id
        trace_event["args"] = self._validate_arguments_and_convert_to_json_string(arguments)

        self._trace_events.append(trace_event)

    @classmethod
    def _validate_arguments_and_convert_to_json_string(cls, arguments: Dict) -> str:
        """
        :param arguments:
        :return: valid json string
        """
        args_json = {}
        if arguments is None:
            return json.dumps(arguments)

        # now we need to make sure that the arguments are a valid json and if so, we put it in
        forbidden_keys = ["password", "pass", "pwd"]
        try:
            for key, value in arguments.items():

                # let's hide creds first
                found_creds = False
                for forbidden_key in forbidden_keys:
                    if forbidden_key.lower() in key.lower():
                        found_creds = True
                        args_json[key] = "value replaced by credential scanner"
                if found_creds:
                    continue

                if isinstance(value, (str, int, bool, float)):
                    args_json[key] = value
                elif isinstance(value, pd.DataFrame):
                    args_json[key] = {
                        "columns": [name for name in value.columns.values],
                        "num_rows": len(value.index)
                    }
                else:
                    try:
                        value = str(value)
                        if len(value) > 10000:
                            raise ValueError("Value too long.")
                        args_json[key] = value
                    except:
                        args_json[key] = f"value of type {str(type(value))} but must be one of: str, int, bool, float."
        except:
            args_json = {"error message": "Could not parse arguments"}

        args_str = json.dumps(args_json)
        args_str = args_str.replace("'", "''")
        return args_str

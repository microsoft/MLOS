#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from collections import deque
import time

class CommunicationChannel:

    def __init__(self):
        self.messages = deque()

    def __len__(self):
        return len(self.messages)

    def submit_message(self, message):
        self.messages.append(message)

    def get_next(self, spin_duration_ms=10):
        while not self.messages:
            time.sleep(spin_duration_ms/1000.0)
        return self.messages.popleft()

    def __iter__(self):
        while True:
            yield self.get_next()

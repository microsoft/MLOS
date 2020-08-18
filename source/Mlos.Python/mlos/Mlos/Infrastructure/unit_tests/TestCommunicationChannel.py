#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import random
import time
from threading import Thread
import unittest


from mlos.Mlos.Infrastructure import CommunicationChannel


class TestCommunicationChannel(unittest.TestCase):


    def test_multithreaded_communication(self):
        """ If it hangs it failed.

        :return:
        """
        communication_channel = CommunicationChannel()

        num_producers = 5
        num_messages = 100

        producers = []
        for i in range(num_producers):
            producer_thread = Thread(target=self.produce_numbers, args=(communication_channel, i, num_messages))
            producers.append(producer_thread)
            producer_thread.start()

        num_completions = 0
        high_water_marks = {i: -1 for i in range(num_producers)}

        for message in communication_channel:
            identity, value = message
            high_water_marks[identity] = max(value, high_water_marks[identity])

            if value == num_messages:
                num_completions += 1
                if num_completions == num_producers:
                    break

    @staticmethod
    def produce_numbers(communication_channel, identity, count):
        for i in range(count+1):
            communication_channel.submit_message((identity, i))
            time.sleep(random.random()/100.0)
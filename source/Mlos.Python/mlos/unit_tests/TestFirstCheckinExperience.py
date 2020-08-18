#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import logging
import unittest

from mlos.Spaces import SimpleHypergrid, CategoricalDimension
from mlos.Logger import create_logger


class TestFirstCheckinExperience(unittest.TestCase):
    """ A suite of tests exposing for folks onboarding to Mlos to get familiar with this code base.


    The idea here is to provide a suite of simple tests that would allow our new-hires to quickly and
    easily commit their first change into the MLOS repository.
    """

    def setUp(self):
        self.logger = create_logger("FirstCheckinExperienceTests")
        self.logger.level = logging.INFO

    def test_randomly_generating_team_member(self):
        self.logger.info("Starting first check in test.")
        mlos_team = SimpleHypergrid(
            name="mlos_team",
            dimensions=[
                CategoricalDimension(name="member", values=["Ed", "Greg", "Sergiy", "Yaser", "Adam"])
            ]
        )

        random_member = mlos_team.random()
        self.assertTrue(random_member in mlos_team)

#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
""" Implements functionality required for aspect oriented connection to the database.


"""

import datetime
from functools import wraps
import logging
import random
import time

import pyodbc  # pylint: disable=import-error

from mlos.Logger import create_logger

def connection_required(use_default_database=False, autocommit=False):
    """ Ensures that the connection is established before the wrapped function executes.

    :return:
    """

    def decorator(wrapped_function):
        @wraps(wrapped_function)
        def wrapper(*args, **kwargs):
            self = args[0]
            self.connect(use_default_database, autocommit)

            if not self.connected:
                logging.error("Failed to connect to the models database")
                raise Exception("Failed to connect to the results database")

            result = wrapped_function(*args, **kwargs)
            return result
        return wrapper
    return decorator


class DatabaseConnector:

    MAX_BACKOFF_SECONDS = 60

    def __init__(self, connection_string=None, logger=None):
        if logger is None:
            logger = create_logger(logger_name="DatabaseConnector")
        self.logger = logger

        self.connection_string = connection_string
        self.connection = None
        self.using_default_database = False

    @property
    def connected(self):
        if self.connection is None:
            return False
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            rows = [row for row in cursor]
            if not rows:
                return False
            return True
        except:
            return False

    def connect(self, timeout_s=None, use_default_database=False, autocommit=False):
        """ Establishes a connection to the database.

        :param timeout_s:
        :return:
        """
        if self.connected:
            if use_default_database == self.using_default_database:
                self.connection.autocommit = autocommit
                return
            self.disconnect()

        assert self.connection_string is not None
        self.connection_string.validate()

        if use_default_database:
            connection_string = self.connection_string.copy()  # TODO: perhaps a bit too hacky
            connection_string.database_name = "master"
        else:
            connection_string = self.connection_string

        max_backoff_in_seconds = 1
        timeout_period_end = datetime.datetime.now() + datetime.timedelta(seconds=timeout_s) if timeout_s is not None else None
        while True:
            if timeout_period_end is not None and datetime.datetime.now() > timeout_period_end:
                raise TimeoutError("Failed to connect to the database within a specified timeout")
            try:
                self.connection = pyodbc.connect(str(connection_string))
                self.connection.autocommit = autocommit
                return
            except:
                self.logger.error("Failed to connect to the database.", exc_info=True)
                # TODO: make that an intelligent choice
                max_backoff_in_seconds = min(max_backoff_in_seconds * 1.07, self.MAX_BACKOFF_SECONDS)
                backoff_in_seconds = random.random() * max_backoff_in_seconds
                time.sleep(backoff_in_seconds)

        self.using_default_database = use_default_database


    def disconnect(self):
        if self.connection is None:
            self.logger.debug("Already disconnected.")
            return

        try:
            self.connection.close()
            self.connection = None
        except:
            self.logger.error("Failed to close the connection", exc_info=True)

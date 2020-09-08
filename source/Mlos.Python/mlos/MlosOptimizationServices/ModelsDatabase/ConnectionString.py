#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import json

from mlos.Logger import create_logger


class ConnectionString:
    """ A class encapsulating the connection string.

    This can get created from a file. I guess in the future we could add an option to also consult the environment
    variables or the command line arguments.
    """

    @classmethod
    def create_from_config_file(cls, config_file_path, logger=None):
        if logger is None:
            logger = create_logger("ConnectionStringBuilder")
        logger.info(f"Creating a connection string from config file: {config_file_path}.")

        with open(config_file_path, 'r') as in_file:
            connection_string_dict = json.load(in_file)

        return ConnectionString(
            host=connection_string_dict["Host"],
            username=connection_string_dict.get("Username", None),
            password=connection_string_dict.get("Password", None),
            trusted_connection=connection_string_dict.get("TrustedConnection", False),
            database_name=connection_string_dict.get("DatabaseName", None),
            connection_timeout=connection_string_dict.get("ConnectionTimeout", None),
            driver=connection_string_dict.get("Driver", None)
        )


    def __init__(
            self,
            host,
            database_name,
            driver,
            username=None,
            password=None,
            trusted_connection=False,
            connection_timeout=None
    ):
        self.host = host
        self.database_name = database_name
        self.driver = driver
        self.username = username
        self.password = password
        self.trusted_connection = trusted_connection
        self.connection_timeout = connection_timeout

    def validate(self):
        assert self.host is not None
        assert self.database_name is not None
        assert self.driver is not None
        assert (self.username is not None and self.password is not None) or (self.trusted_connection is True)


    def __repr__(self):
        self.validate()

        return_string = f"Driver={{{self.driver}}}; Server={self.host}; Database={self.database_name};"

        if self.trusted_connection:
            return_string += " Trusted_Connection=yes;"
        else:
            return_string += f" UID={self.username}; PWD={self.password};"

        # TODO: incorporate connection timeout
        return return_string

    def copy(self):
        return ConnectionString(
            host=self.host,
            database_name=self.database_name,
            driver=self.driver,
            username=self.username,
            password=self.password,
            trusted_connection=self.trusted_connection,
            connection_timeout=self.connection_timeout
        )

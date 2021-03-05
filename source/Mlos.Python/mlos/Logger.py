#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import logging
import time


class BufferingHandler(logging.StreamHandler):
    def __init__(self):
        logging.StreamHandler.__init__(self)
        self.buffered_log_records = []
        self.level = None

    def setLevel(self, level):
        self.level = level

    def set_level_by_name(self, new_level_name):
        try:
            self.level = logging._nameToLevel[new_level_name] # pylint: disable=protected-access
        except:
            pass

    def emit(self, record):
        if self.level <= record.levelno:
            self.buffered_log_records.append(record)

    def get_records(self, clear_buffer=False):
        records = self.buffered_log_records
        if clear_buffer:
            self.clear()
        return records

    def clear(self):
        self.buffered_log_records = []

    def dump_to_file(self, output_file_path):
        with open(output_file_path, 'a+') as out_file:
            for record in self.buffered_log_records:
                out_file.write(self.format(record=record))


def create_logger(logger_name, create_console_handler=True, create_file_handler=False, create_buffering_handler=False, logging_level=logging.INFO):
    """Create a new logger.

    Parameters
    ----------
    logger_name : str
        Name for the new logger.
    create_console_handler : boolean, default=True
        Whether to create a stream handler and add to the logger.
    create_file_handler : boolean, default=False
        Whether to add a file handler. If True, logs are stored in ``<logger_name>.log``.
    create_buffering_handler : boolean, default=False
        Whether to add a buffering handler. If True, return value will be
        logger, buffering_handler instead of just the logger.
    logging_level : int, default=logging.INFO
        Log level.
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging_level)
    logger.propagate = False
    formatter = logging.Formatter('%(asctime)s - %(name)26s - %(levelname)7s - [%(filename)20s:%(lineno)4s - %(funcName)25s() ] %(message)s')
    formatter.converter = time.gmtime
    formatter.datefmt = '%m/%d/%Y %H:%M:%S'

    if create_console_handler:
        if not any([isinstance(handler, logging.StreamHandler) for handler in logger.handlers]):
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging_level)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

    if create_file_handler:
        file_handler = logging.FileHandler(logger_name + ".log")
        file_handler.setLevel(logging_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    buffering_handler = None
    if create_buffering_handler:
        buffering_handler = BufferingHandler()
        buffering_handler.setLevel(logging_level)
        buffering_handler.setFormatter(formatter)
        logger.addHandler(buffering_handler)

    # TODO: Fix this, as sometimes we are returning a tuple + logger and sometimes just the logger.
    if create_buffering_handler:
        return logger, buffering_handler

    return logger

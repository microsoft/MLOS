#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#


class MlosException(Exception):
    """Base class for all exceptions specific to Mlos. """


class InvalidDimensionException(MlosException):
    """ Raised when a dimension inappropriate for the context is encountered. """


class InvalidPointException(MlosException):
    """ The point is invalid for a given operation. """


class PointOutOfDomainException(InvalidPointException):
    """ The point does not belong to the specified domain. """

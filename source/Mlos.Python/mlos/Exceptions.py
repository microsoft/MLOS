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


class UnableToProduceGuidedSuggestionException(MlosException):
    """Thrown by any utility function optimizer unable to produce a guided suggestion.

    This is to explicitly instruct the experiment designer that a random suggestion should be produced. This can be reflected in
    the suggestion's metadata. Furthermore, having this information we can now assert that a portion of suggestions is non-random.
    """


class UtilityValueUnavailableException(UnableToProduceGuidedSuggestionException):
    """Thrown by utility function optimizer unable to produce a guided suggestion due to utility function productin no values.

    This is useful to ascertain that the model is producing at least some predictions. Models can fail to produce suggestion either if
    they have not been fitted, or because they don't recognize feature names or because feature values are outside their domains.

    This later mode of failure went undetected for GlowWormSwarmOptimizer for a few months, as it continued returning random suggestions
    implicitly when no predictions were available from the surrogate model.
    """

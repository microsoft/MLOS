#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
"""
Space converters init file.

Space converters are helper functions that translate a
:py:class:`ConfigSpace.ConfigurationSpace` that :py:mod:`mlos_core` Optimizers take
as input to the underlying Optimizer's parameter description language (in case it
doesn't use :py:class:`ConfigSpace.ConfigurationSpace`).

They are not generally intended to be used directly by the user.

See Also
--------
:py:mod:`mlos_core` : for an overview of configuration spaces in ``mlos_core``.
"""

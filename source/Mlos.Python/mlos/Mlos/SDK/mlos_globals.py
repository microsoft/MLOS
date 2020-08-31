#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from mlos.Mlos.Infrastructure import CommunicationChannel, SharedConfig
from mlos.Mlos.SDK import MlosGlobalContext # TODO: move this to Infrastructure

def init_mlos_global_context():
    global mlos_global_context  # pylint: disable=global-variable-undefined
    mlos_global_context = MlosGlobalContext(
        communication_channel=CommunicationChannel(),
        shared_config=SharedConfig()
    )

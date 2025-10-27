#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
from pydantic import BaseModel


class ExperimentExplanationRequest(BaseModel):
    experiment_id: str

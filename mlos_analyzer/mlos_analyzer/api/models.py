from pydantic import BaseModel

class ExperimentExplanationRequest(BaseModel):
    experiment_id: str

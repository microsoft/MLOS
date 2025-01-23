from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .models import ExperimentExplanationRequest
from ..core.storage import storage
import logging

app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/experiments")
def get_experiments():
    return list(storage.experiments.keys())

@app.get("/experiment_results/{experiment_id}")
def get_experiment_results(experiment_id: str):
    try:
        exp = storage.experiments[experiment_id]
        return exp.results_df.to_dict(orient="records")
    except KeyError:
        raise HTTPException(status_code=404, detail="Experiment not found")

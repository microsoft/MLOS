from datetime import datetime, timedelta
import time
import schedule
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
from openai import AzureOpenAI
from fastapi import FastAPI,  Request, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
import pandas as pd
import json
from pathlib import Path
from azure.mgmt.compute import ComputeManagementClient
from azure.identity import DefaultAzureCredential
from mlos_bench.storage import from_config
from copy import deepcopy
import subprocess
import logging
import asyncio
from fastapi.middleware.cors import CORSMiddleware
import re
import json5

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load global configuration
base_dir = Path(__file__).resolve().parent
global_config_path = base_dir / 'global_config_azure.json'
with global_config_path.open() as f:
    global_config = json.load(f)
    subscription_id = global_config['subscription']

# Load the storage config and connect to the storage
storage_config_path = "config/storage/mlos-mysql-db.jsonc"
try:
    storage = from_config(config_file=storage_config_path)
except Exception as e:
    raise HTTPException(
        status_code=500, detail=f"Error loading storage configuration: {e}"
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

def count_categorical_values(df: pd.DataFrame) -> str:
    categorical_counts = {}
    for col in df.select_dtypes(include=['object', 'category']).columns:
        counts = df[col].value_counts().to_dict()
        categorical_counts[col] = counts

    count_str = "Categorical Counts:\n"
    for col, counts in categorical_counts.items():
        count_str += f"{col}:\n"
        for value, count in counts.items():
            count_str += f"  {value}: {count}\n"

    return count_str

# Load credentials from the JSON file
with open('azure_openai_credentials.json', 'r') as file:
    credentials = json.load(file)

# Try to create the AzureOpenAI client
try:
    client = AzureOpenAI(
        azure_endpoint=credentials['azure_endpoint'],
        api_key=credentials['api_key'],
        api_version=credentials['api_version']
    )
except Exception as e:
    print("Error creating AzureOpenAI client:", e)
class ExperimentExplanationRequest(BaseModel):
    experiment_id: str

@ app.post("/get_experiment_explanation")
def get_experiment_explanation(request: ExperimentExplanationRequest):
    experiment_id = request.experiment_id
    try:
        exp = storage.experiments[experiment_id]
        # Taking only the first 10 rows for simplicity
        df = exp.results_df.tail(10)
        experiment_data = df.to_dict(orient='records')

        df_head = exp.results_df.head(10)
        experiment_data_head = df_head.to_dict(orient='records')

        df_des = exp.results_df.describe()
        experiment_data_des = df_des.to_dict(orient='records')

        count_str = count_categorical_values(df)

        prompt = f"Explain the following experiment data: First 10 rows {experiment_data_head} last 10 {experiment_data} & descriptive stats {experiment_data_des} & categorical vars counts {count_str}. Give me params to complement config. params present in the data. Also explain what each param does and params for MySQL config that would complement what we have and can boost preformance if tuned. Explain which are dangreous to tune as it might fail the server. Also talk about parameters that are safe to tune. Talk about each in list format so that you are listing all information relevant to a param under its name"

        response = client.chat.completions.create(
            model="gpt4o",  # model = "deployment_name".
            messages=[
                {"role": "assistant",
                    "content":  prompt}
            ],
            max_tokens=1000
        )

        explanation = response.choices[0].message.content.strip()
        print(explanation)
        return {"explanation": explanation}
    except KeyError:
        raise HTTPException(status_code=404, detail="Experiment not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

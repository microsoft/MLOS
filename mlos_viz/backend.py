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

selected_config_path = ""
# Load MySQL tunable parameters configuration
mysql_tunables_path = base_dir / \
    'config/environments/apps/mysql/mysql-tunables.jsonc'
with mysql_tunables_path.open() as f:
    mysql_tunables = json.load(f)


class ControlDataRunRequest(BaseModel):
    selected_skus: list
    selected_purpose: str
    selected_benchbase_config_file: str
    num_nodes: int
    num_times_per_day: int
    experiment_name: str
    exp_id: str
    terminals: int
    scalefactor: int


@app.post("/run_control_data")
def run_control_data(request: ControlDataRunRequest):
    try:
        bench_path = 'config/cli/cli-azure-mysql-flex-benchbase-bench.jsonc'
        times_per_day = request.num_times_per_day

        base_dir = Path(__file__).resolve().parent

        def write_vm_sizes_b(selected_skus):
            vm_sizes_path = base_dir / "vm_sizes.txt"
            with vm_sizes_path.open("w") as f:
                for sku in selected_skus:
                    f.write(f"{sku}\n")
            logger.info(f"VM sizes written to {vm_sizes_path}")

        def run_experiment_b(vm_size, num_nodes):

            #############################################################
            # Path to the input jsonc file
            input_file_path = base_dir / "config/environments/apps/mysql/mysql-tunables.jsonc"
            output_file_path = base_dir / "default_mysql_tunables.json"

            # Read the input file
            with input_file_path.open() as file:
                tunables_data = json.load(file)

            # Extract default values from the input data
            default_values = {
                "$schema": "https://raw.githubusercontent.com/microsoft/MLOS/main/mlos_bench/mlos_bench/config/schemas/tunables/tunable-values-schema.json"
            }

            for category, data in tunables_data.items():
                for param_name, param_data in data["params"].items():
                    default_values[param_name] = param_data.get(
                        "default", None)

            # Write the default values to the JSON file
            with output_file_path.open('w') as file:
                json.dump(default_values, file, indent=4)

            print(
                f"Default configuration file generated at {output_file_path}")
            ####################################################


            for i in range(1, num_nodes + 1):

                config_filename = base_dir / \
                    f'temp_config_{vm_size}_{i}_{request.exp_id}.json'
                # --tunable_values opt-d2ads-v5.jsonc'
                # --tunable_values default_mysql_tunables.json
                # --tunable_values default_mysql_tunables_twit_better.jsonc
                command = f'mlos_bench --config {bench_path} --globals {config_filename}'


                if not config_filename.exists():
                    logger.error(
                        f"Configuration file {config_filename} does not exist. Skipping experiment for {vm_size}.")
                    return

                session_name = f"control_{vm_size}_{i}_{request.exp_id}"
                tmux_command = f"tmux new-session -d -s {session_name} \"stdbuf -oL -eL {command} > control_log_{vm_size}_{i}_{request.exp_id}.log 2>&1\""
                print("RUNNING COMMAND : ", tmux_command)
                try:
                    result = subprocess.run(
                        tmux_command, shell=True, capture_output=True, text=True, check=True)
                    logger.info(f"Started tmux session: {session_name}")
                    logger.info(f"Command output: {result.stdout}")
                    logger.error(f"Command error (if any): {result.stderr}")
                except subprocess.CalledProcessError as e:
                    logger.error(
                        f"Failed to start tmux session {session_name}: {e.stderr}")

        # Run the scheduler in a separate thread or process

        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(1)

        def run_all_experiments_b(selected_skus):
            if not selected_skus:
                logger.error("No VM sizes found. Skipping experiments.")
                return
            os.environ['MLOS_BENCH_SKIP_SCHEMA_VALIDATION'] = 'true'
            for vm_size in selected_skus:
                run_experiment_b(vm_size, request.num_nodes)

        # cleaned_user_input_experiment_name = f'benchmark-control'

        # generate_configurations(request.selected_skus, selected_tunables, selected_config_file,
        #                         request.selected_benchbase_config_file, cleaned_user_input_experiment_name, request.selected_purpose)

        def schedule_experiments(selected_skus, times_per_day):
            start_time = datetime.now() + timedelta(seconds=10)
            interval = 24 * 3600 / times_per_day  # interval in seconds

            logger.info(
                f"First run scheduled at {start_time.strftime('%H:%M:%S')}")

            for day in range(7):  # Loop through each day of the week
                day_start_time = start_time + timedelta(days=day)
                for i in range(times_per_day):
                    scheduled_time = (
                        day_start_time + timedelta(seconds=i * interval)).strftime("%H:%M:%S")
                    schedule.every().day.at(scheduled_time).do(
                        run_all_experiments_b, selected_skus)
                    logger.info(
                        f"Scheduled experiment run at {scheduled_time} on day {day_start_time.strftime('%A')}")

        # Write VM sizes to file
        write_vm_sizes(request.selected_skus)

        # Generate configurations for the provided SKUs before running experiments
        # Load MySQL tunable parameters configuration
        mysql_tunables_path = base_dir / \
            'config/environments/apps/mysql/mysql-tunables.jsonc'
        with mysql_tunables_path.open() as f:
            mysql_tunables = json.load(f)

        # Extract tunable parameter groups
        # selected_tunables = list(mysql_tunables.keys())
        selected_tunables = ["mysql-misc"]
        # selected_tunables = ["security-and-connection-settings"]

        selected_config_file = 'cli-azure-mysql-flex-benchbase-bench.jsonc'

        for sku in request.selected_skus:
            for i in range(1, request.num_nodes + 1):
                # TODO FIX NAME
                # Used for resource naming
                cleaned_user_input_experiment_name = f'{request.experiment_name}-{i}'
                # If defined will not use resource naming as experiment name
                exp_id = f'{request.exp_id}-{i}'

                # for sku in request.selected_skus:
                config_named = f'temp_config_{sku}_{i}_{request.exp_id}.json'

                generate_configurations(sku, selected_tunables, selected_config_file,
                                        request.selected_benchbase_config_file, cleaned_user_input_experiment_name, request.selected_purpose, exp_id=exp_id, terminals=request.terminals, scalefactor=request.scalefactor, config_named=config_named)

        schedule_experiments(request.selected_skus, times_per_day)


        import threading
        scheduler_thread = threading.Thread(target=run_scheduler)
        scheduler_thread.start()

        return {"status": "success", "message": "Control data experiments are scheduled"}

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise HTTPException(
            status_code=500, detail="An error occurred while running control data experiments")

class ExperimentRunRequest(BaseModel):
    selected_skus: list
    selected_tunables: list
    selected_config_path: str
    selected_benchbase_config_file: str
    selected_experiment_name: str
    selected_purpose: str
    trial_repeat_count: int
    max_iterations: int
    exp_id: str
    terminals: int
    scalefactor: int

@app.get("/vm_skus")
def get_vm_skus():
    credentials = DefaultAzureCredential()
    compute_client = ComputeManagementClient(credentials, subscription_id)
    skus = compute_client.resource_skus.list()
    vm_skus = sorted(
        {sku.name for sku in skus if sku.resource_type == "virtualMachines"}
    )
    return vm_skus

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

@app.post("/run_experiments")
def run_experiments(request: ExperimentRunRequest):
    selected_config_path = request.selected_config_path

    os.environ['CONFIG_PATH_CLI_GUI'] = "config/cli/"
    os.environ['CONFIG_PATH_CLI_GUI'] = str(selected_config_path)

    write_vm_sizes(request.selected_skus)
    generate_configurations(
        request.selected_skus,
        request.selected_tunables,
        request.selected_config_path,
        request.selected_benchbase_config_file,
        request.selected_experiment_name,
        request.selected_purpose,
        exp_id=request.exp_id,
        terminals=request.terminals,
        scalefactor=request.scalefactor,
        # TODO for each sku in selected_skus, currently defaults have to be set manually depending on flex instance and then based on one specific sku defaults you can test (did a quick roll back on being able to launch many skus at once since tunables file will change)
        config_named=f'temp_config_{request.selected_skus[0]}_{request.exp_id}.json'
    )
    print("Running the experiments script...")

    # Set the config path environment variable
    os.environ['CONFIG_PATH_CLI_GUI'] = "config/cli/"
    os.environ['CONFIG_PATH_CLI_GUI'] = str(selected_config_path)

    try:
        for vm_size in request.selected_skus:
            config_path = os.environ.get('CONFIG_PATH_CLI_GUI')
            print(f'Using config path: {config_path}')
            config_filename = f'temp_config_{vm_size}_{request.exp_id}.json'
            command = f'mlos_bench --config {config_path} --globals {config_filename}'

            if (request.trial_repeat_count != 0 and request.max_iterations != 0):
                command += f' --trial-config-repeat-count {request.trial_repeat_count} --max_trials {request.max_iterations}'

            tmux_command = (
                f'tmux new-session -d -s "Session_{vm_size}_{request.exp_id}" "stdbuf -oL -eL {command} > log_{vm_size}_{request.exp_id}.log 2>&1"'
            )
            print(f'Running command: {tmux_command}')

            os.environ['MLOS_BENCH_SKIP_SCHEMA_VALIDATION'] = 'true'
            result = subprocess.run(
                tmux_command, shell=True)

        # Run the external script
        # result = subprocess.run(
        #     ['bash', 'run_experiments.sh', str(request.trial_repeat_count), str(request.max_iterations), request.selected_experiment_name], check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        print("All tmux sessions started.")
        print("External script executed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred: {e}")
        return {"status": "failed", "message": f"{e}"}
    # Simulate running experiments
    return {"status": "success", "message": "Experiments are running"}


log_directory = base_dir
log_file_extension = ".log"
check_interval = 300  # 5 minutes in seconds

error_patterns = [
    re.compile(r'ERROR'),
    re.compile(r'FAILED'),
    re.compile(r'EXCEPTION'),
    re.compile(r'exception'),
    re.compile(r'Error'),
    re.compile(r'error'),
    re.compile(r'Traceback'),
    re.compile(r'TRACEBACK'),
    re.compile(r'(None, None)'),
    re.compile(r'Final score: None')
]

# Function to parse log file for errors


def parse_log_file(file_path):
    errors = []
    with open(file_path, 'r') as log_file:
        for line_number, line in enumerate(log_file, 1):
            for pattern in error_patterns:
                if pattern.search(line):
                    errors.append((line_number, line.strip()))
                    break
    set_errors = set(errors)
    errors = list(set_errors)
    return errors

# Function to list all .log files and their errors


def get_all_log_errors():
    log_files = [f for f in os.listdir(
        log_directory) if f.endswith(log_file_extension)]
    all_errors = {}
    for log_file in log_files:
        file_path = os.path.join(log_directory, log_file)
        errors = parse_log_file(file_path)
        if errors:
            all_errors[log_file] = errors
    return all_errors


@app.get("/log_errors")
def get_log_errors():
    try:
        all_errors = get_all_log_errors()
        return all_errors
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving log errors: {e}")

@app.post("/kill_all_sessions")
def kill_all_sessions():
    try:
        # Correctly call the tmux command directly
        result = subprocess.run(['tmux', 'kill-server'],
                                check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return {"status": "success", "message": "All tmux sessions killed"}
    except subprocess.CalledProcessError as e:
        print(f"Error occurred: {e}")
        return {"status": "error", "message": "Failed to kill tmux sessions", "details": str(e)}

# Endpoint to list all tmux sessions


@app.get("/list_tmux_sessions")
def list_tmux_sessions():
    try:
        result = subprocess.run(
            ['tmux', 'list-sessions'], capture_output=True, text=True)
        sessions = result.stdout.strip().split('\n')
        return {"sessions": sessions}
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list tmux sessions: {str(e)}")


class KillSessionRequest(BaseModel):
    session_name: str


@app.post("/kill_tmux_session")
async def kill_tmux_session(request: KillSessionRequest):
    session_name = request.session_name
    try:
        result = subprocess.run(
            ['tmux', 'kill-session', '-t', session_name], check=True, capture_output=True, text=True)
        return {"status": "success", "message": f"Tmux session '{session_name}' killed successfully"}
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to kill tmux session '{session_name}': {str(e)}")


def write_vm_sizes(selected_skus):
    vm_sizes_path = base_dir / "vm_sizes.txt"
    with vm_sizes_path.open("w") as f:
        for sku in selected_skus:
            f.write(f"{sku}\n")
    print(f"VM sizes written to {vm_sizes_path}")


def generate_configurations(selected_skus, selected_tunables, selected_config_file, selected_benchbase_config_file, cleaned_user_input_experiment_name, selected_purpose, config_named="", exp_id="", terminals=0, scalefactor=0):
    with open('base_config.json', 'r') as file:
        base_config = json.load(file)

    if "benchbase" in selected_config_file:
        with open('benchbase_template.json', 'r') as file:
            base_config = json.load(file)

    # Read VM sizes from the vm_sizes.txt file
    with open('vm_sizes.txt', 'r') as file:
        vm_sizes = [line.strip() for line in file.readlines()]

    import random
    import string

    random_letters = ''.join(random.choice(
        string.ascii_uppercase) for _ in range(4)).lower()

    # Generate a configuration file for each VM size
    for vm_size in vm_sizes:

        valid_vm_size = vm_size.replace('_', '-').lower()
        parsed_values = valid_vm_size.split('-')[1:]
        parsed_value = ''.join(parsed_values)

        benchmark_name = extract_benchmark_name(selected_benchbase_config_file)
        config = deepcopy(base_config)

        # Update configuration with experiment details
        if exp_id == "":
            config['experiment_id'] = f"{parsed_value}-{cleaned_user_input_experiment_name}"
            config['deploymentName'] = f"{parsed_value}-deploy-{cleaned_user_input_experiment_name}-{random_letters}"
        else:
            config['experiment_id'] = f"{parsed_value}-{exp_id}"
            config['deploymentName'] = f"{parsed_value}-deploy-{exp_id}-{random_letters}"


        config['serverEdition'] = selected_purpose

        if "benchbase" not in selected_config_file:
            config['vmName_server'] = f"{parsed_value}-s-{cleaned_user_input_experiment_name}"
            config['vmName_client'] = f"{parsed_value}-c-{cleaned_user_input_experiment_name}"
            config['vmSize_server'] = vm_size
            config['vmSize_client'] = vm_size
            config['serverName'] = f"{parsed_value}-s-{cleaned_user_input_experiment_name}"

        if "benchbase" in selected_config_file:
            config['vmName_client'] = f"{parsed_value}-client-{cleaned_user_input_experiment_name}"
            config['vmName_server'] = f"{parsed_value}-server-{cleaned_user_input_experiment_name}"
            config['vmSize'] = vm_size
            config['benchmark'] = "benchbase"
            config['serverName'] = f"{parsed_value}-flex-{cleaned_user_input_experiment_name}"
            config['serverSkuName'] = vm_size
            config['BENCHBASE_BENCHMARK'] = benchmark_name
            config['BENCHBASE_CONFIG_FILE'] = selected_benchbase_config_file
            config['BENCHBASE_SCALE_FACTOR'] = scalefactor
            config['BENCHBASE_TERMINALS'] = terminals

        # Include only the selected tunable parameter group names
        config['tunable_params_map'] = {
            "provision": [],
            "linux-boot": [],
            "linux-runtime": [],
            "mysql": [tunable for tunable in selected_tunables]
        }

        config_filename = config_named
        if config_named == "":
            config_filename = base_dir / f'temp_config_{vm_size}.json'

        with open(config_filename, 'w') as config_file:
            json.dump(config, config_file, indent=4)

        # # change params in ,mysql-flex-server.jsonc
        # path_tunables_change = base_dir / \
        #     'config/environments/apps/mysql/mysql-flex-server.jsonc'

        # # Read the JSONC file
        # with open(path_tunables_change, 'r') as file:
        #     config_flex = json.load(file)

        # # Deep copy the original configuration to avoid unintended modifications
        # config_flex_copy = deepcopy(config_flex)

        # # Update the tunable_params in the copied config
        # if 'config' in config_flex_copy:
        #     config_flex_copy['config']['tunable_params'] = [
        #         tunable for tunable in selected_tunables]

        # else:
        #     print("The key 'config' not found in the JSON file.")

        # # Save the updated JSON back to the file
        # with open(path_tunables_change, 'w') as file:
        #     json.dump(config_flex_copy, file, indent=4)

        print(f"Generated configuration for {vm_size} in {config_filename}")

def extract_benchmark_name(config_file):
    return config_file.split("-")[0]


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
            #           messages=[
            #     {"role": "system", "content": "You are a helpful assistant."},
            #     {"role": "user", "content": "Does Azure OpenAI support customer managed keys?"},
            #     {"role": "assistant",
            #         "content": "Yes, customer managed keys are supported by Azure OpenAI."},
            #     {"role": "user", "content": "Do other Azure AI services support this too?"}
            # ]
            max_tokens=4096
        )

        explanation = response.choices[0].message.content.strip()
        print(explanation)
        return {"explanation": explanation}
    except KeyError:
        raise HTTPException(status_code=404, detail="Experiment not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

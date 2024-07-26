

### MLOS Viz Panel

3. Set up Azure credentials for OpenAI and Azure Compute:
   - Create a `azure_openai_credentials.json` file with the following structure:
     ```json
     {
       "azure_endpoint": "<your_azure_endpoint>",
       "api_key": "<your_api_key>",
       "api_version": "<api_version>"
     }
     ```
   - Ensure you have configured Azure credentials for the `ComputeManagementClient` to access VM SKUs.

  - Create `global_config_storage.jsonc`
    ```json
     {
          "host": "x.mysql.database.azure.com",
          "username": "mlos",
          "password": "x",
          "database": "x"
      }
     ```

  - Create `global_config_azure.json`
    ```json
    {
        "subscription": "x",
        "tenant": "x",
        "storageAccountKey": "x"
    }
     ```

4. Set up the necessary configuration files in the `config/` directory as per your environment.

## Usage

### Running the Backend

1. Navigate to the project directory.
2. Start the FastAPI server:
   ```bash
   uvicorn backend:app --reload
   ```

### Running the Frontend

1. Navigate to the project directory.
2. Start the Streamlit application:
   ```bash
   streamlit run frontend.py
   ```

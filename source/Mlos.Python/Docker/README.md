# Mlos Python Docker Notes

We use `docker` to package Mlos and its Python dependencies together with a database instance (in this case SqlServer) for storing optimizer models and experiment data.

This document contains a few brief notes on that setup.

## Creating a secrets file

Inside the [`Secrets`](../Secrets) directory there is a [`sample_docker_connection_string.json`](../Secrets/sample_docker_connection_string.json).
It is complete except for the `Password` field, which we don't want checked into the repository.

1. Create a good password.

1. Make a copy of that file at `local_docker_connection_string.json`

  ```shell
  cp sample_docker_connection_string.json local_docker_connection_string.json
  ```

2. Edit the new file to include your new password:

  ```json
  {
    "Host": ".",
    "Username": "sa",
    "Password": "*YouKnowWhatToPutHere*",
    "DatabaseName": "MlosModels",
    "TrustedConnection": false,
    "Driver": "ODBC Driver 17 for SQL Server"
  }
  ```


## Building the image

For the `SA_PASSWORD` below use the same password as the one used in the secrets file above.

```shell
cd $MLOS_ROOT/source/Mlos.Python
docker build -f Docker/Dockerfile -t mssql-server-linux-with-mlos-python --build-arg SA_PASSWORD=*YouKnowWhatToPutHere* .
```

> Note: the trailing `.` in the preceeding command is important.

## Other useful commands

- List images:

  ```shell
  docker images:
  ```

- Start a container named `MlosOptimizerService` from the image we built earlier:

  ```shell
  docker run -p1433:1433 --name MlosOptimizerService mssql-server-linux-with-mlos-python
  ```

- Connect to the container named `MlosOptimizerService`:

  ```shell
  docker exec -it MlosOptimizerService /bin/bash
  ```

- Stop the container named `MlosOptimizerService`:
  
  ```shell
  docker stop MlosOptimizerService
  ```

- Remove that container:

  ```shell
  docker container rm MlosOptimizerService
  ```

## Notes and considerations

We initialize the schema at build time of the docker image so that the containers can be stopped and restarted without wiping all the data from them.

For that we need a way to:
1. Start SqlServer from within the Dockerfile
2. Execute `sqlcmd` to create the schema
3. Stop SqlServer
All of this happens in the Dockerfile during the `docker build` process.

An alternative is to use persistent volumes.  For instance:

1. Create a persistent volumes:

  ```shell
  docker volume create MlosOptimizerService
  ```

2. Use it during docker container creation:

  ```shell
  docker run -p1433:1433 --name MlosOptimizerService --volume MlosOptimizerService:/var/opt/mssql mssql-server-linux-with-mlos-python
  ```


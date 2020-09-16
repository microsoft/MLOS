# TODO: decide on a specific version. Don't use the 'latest tag'
#
FROM microsoft/mssql-server-linux:latest

# Install python3.7
# We first need to add the deadsnakes repository that contains python3.7 packages.
# Secondly we install python3.7 and pip.
# Thirdly, we add all packages required for pyodbc to work (thats the line that ends with unxodbc-dev).
# Lastly, we purge the apt-get cache to not bloat the image.
#
RUN apt-get -y update && \
    apt-get install -y software-properties-common && \
    add-apt-repository -y ppa:deadsnakes/ppa && \
    apt-get -y update && \
    apt-get install -y python3.7 python3-pip && \
    apt-get install -y build-essential libssl-dev libffi-dev python3-dev python3.7-dev unixodbc-dev && \
    rm -rf /var/lib/apt/lists/*

# Install python3.7 pip
#
RUN python3.7 -m pip install pip
RUN python3.7 -m pip install --upgrade pip

# Copy Mlos.Python code
RUN mkdir -p /usr/src/Mlos.Python
WORKDIR /usr/src/

# Copy requirements first
# COPY ./requirements.txt ./Mlos.Python/requirements.txt
# RUN python3.7 -m pip install  /usr/src/Mlos.Python/requirements.txt

COPY . ./Mlos.Python
RUN python3.7 -m pip install ./Mlos.Python

# Let's set the environment variables
#
ENV ACCEPT_EULA=Y

# This has to be supplied during build like so: docker build --build-arg SA_PASSWORD=YourStrongPassword
#
ARG SA_PASSWORD=DEFAULT_SA_PASSWORD

# Let's start SQL Server and populate the schema
#
RUN (/opt/mssql/bin/sqlservr --accept-eula & ) | grep -q "Service Broker manager has started" && \
    /opt/mssql-tools/bin/sqlcmd -S127.0.0.1 -Usa -P${SA_PASSWORD} -i ./Mlos.Python/mlos/MlosOptimizationServices/ModelsDatabase/SQLScripts/Schema.sql

# Expose the optimizer's port
#
EXPOSE 50051

CMD /opt/mssql/bin/sqlservr & \
    cd Mlos.Python; start_optimizer_microservice launch

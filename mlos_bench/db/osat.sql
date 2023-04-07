--
-- Copyright (c) Microsoft Corporation.
-- Licensed under the MIT License.
--

DROP TABLE IF EXISTS benchmark CASCADE;
DROP TABLE IF EXISTS benchmark_status CASCADE;
DROP TABLE IF EXISTS environment CASCADE;
DROP TABLE IF EXISTS composite_environment CASCADE;
DROP TABLE IF EXISTS experiment CASCADE;
DROP TABLE IF EXISTS tunable_parameter CASCADE;
DROP TABLE IF EXISTS tunable_value CASCADE;

DROP TYPE IF EXISTS string_id_t CASCADE;
DROP TYPE IF EXISTS benchmark_status_t CASCADE;

CREATE DOMAIN string_id_t AS varchar(255) NOT NULL;

CREATE TYPE benchmark_status_t AS ENUM (
    'pending', 'running', 'failed', 'canceled', 'completed');

-- Each environment is a collection of scripts and configuration templates
-- required to run an experiment, along with a (Python) class name that
-- contains the code that actually launches the scripts and runs the benchmarks.
CREATE TABLE environment (
    id string_id_t PRIMARY KEY,
    name text NOT NULL,
    class string_id_t,              -- Python class that implements the experiment
    config_path text,               -- (relative) git path to scripts and config templates
    config_version text,            -- git branch or commit id of the scripts
    parameters json,                -- Static parameters to plug into the config
    cost float                      -- Cost of changing the parameters' values.
);

-- Composite environments are trees of environment instances.
-- environment.class of the root environment is a (Python) class that
-- implements the composition.
CREATE TABLE composite_environment (
    root_id string_id_t REFERENCES environment(id),
    parent_id string_id_t REFERENCES environment(id),
    child_id string_id_t REFERENCES environment(id),

    PRIMARY KEY (root_id, parent_id, child_id)
);

-- An experiment is a series of benchmarks for the given environment.
CREATE TABLE experiment (
    id string_id_t PRIMARY KEY,
    environment_id string_id_t REFERENCES environment(id),
    ts timestamp NOT NULL DEFAULT now(),
    parameters json                 -- Parameters to plug into the environment config
);

CREATE TABLE benchmark (
    id serial NOT NULL PRIMARY KEY,
    experiment_id string_id_t REFERENCES experiment(id),
    ts timestamp NOT NULL DEFAULT now(),
    parameters json,                -- Benchmark-specific parameters, e.g., VM id (NOT tunables!)
    final_status benchmark_status_t,
    final_result float
);

CREATE TABLE benchmark_status (
    benchmark_id integer NOT NULL REFERENCES benchmark(id),
    ts timestamp NOT NULL DEFAULT now(),
    status benchmark_status_t NOT NULL,
    result float,
    telemetry json,

    PRIMARY KEY (benchmark_id, ts)
);

-- Tunable parameters' descriptions.
-- Should be deserializeable into ConfigSpace.
CREATE TABLE tunable_parameter (
    environment_id string_id_t REFERENCES environment(id),
    name string_id_t,
    type string_id_t,
    range json,
    default_value json,

    PRIMARY KEY (environment_id, name)
);

-- Values of the tunables for a given benchmark.
-- (Maybe, store as JSON column in the benchmark table?)
CREATE TABLE tunable_value (
    benchmark_id integer NOT NULL REFERENCES benchmark(id),
    environment_id string_id_t REFERENCES environment(id),
    name string_id_t,
    value json,

    PRIMARY KEY (benchmark_id, name),
    FOREIGN KEY(environment_id, name)
	    REFERENCES tunable_parameter(environment_id, name)
);

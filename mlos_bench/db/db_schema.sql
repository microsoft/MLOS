--
-- Copyright (c) Microsoft Corporation.
-- Licensed under the MIT License.
--

-- DB schema for storing MLOS benchmarking results.
-- The syntax works for SQLite3, DuckDB, PostgreSQL, and MySQL / MariaDB.

DROP TABLE IF EXISTS trial_telemetry;
DROP TABLE IF EXISTS trial_result;
DROP TABLE IF EXISTS trial_param;
DROP TABLE IF EXISTS config_param;
DROP TABLE IF EXISTS trial;
DROP TABLE IF EXISTS config;
DROP TABLE IF EXISTS experiment;
DROP TABLE IF EXISTS param_type;

-- Type information for tunable parameters and benchmark/telemetry metrics.
CREATE TABLE param_type (
    param_id VARCHAR(255) NOT NULL,
    data_type VARCHAR(32) NOT NULL,  -- One of {int, float, categorical}
    default_value VARCHAR(255),
    meta VARCHAR(1023),  -- metadata JSON (range or categories).

    PRIMARY KEY (param_id)
);

CREATE TABLE experiment (
    exp_id VARCHAR(255) NOT NULL,
    descr TEXT,
    metric_id VARCHAR(255) NOT NULL,  -- Metric we're optimizing for.
    git_repo VARCHAR(255) NOT NULL,
    git_commit VARCHAR(40) NOT NULL,

    PRIMARY KEY (exp_id)

    -- TODO: Enable when we pre-populate the `param_type` table:
    -- FOREIGN KEY (metric_id) REFERENCES param_type(param_id)
);

CREATE TABLE config (
    config_id INTEGER NOT NULL,
    config_hash VARCHAR(40) NOT NULL,

    PRIMARY KEY (config_id)
    -- UNIQUE (config_hash)
);

CREATE TABLE trial (
    exp_id VARCHAR(255) NOT NULL,
    trial_id INTEGER NOT NULL,
    config_id INTEGER NOT NULL,
    ts_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    ts_end TIMESTAMP,
    -- Should match the text IDs of `mlos_bench.environment.Status` enum:
    trial_status VARCHAR(16) NOT NULL,

    PRIMARY KEY (exp_id, trial_id),
    FOREIGN KEY (exp_id) REFERENCES experiment(exp_id),
    FOREIGN KEY (config_id) REFERENCES config(config_id)
);

-- Values of the tunable parameters of the experiment,
-- fixed for a particular trial config.
CREATE TABLE config_param (
    config_id INTEGER NOT NULL,
    param_id VARCHAR(255) NOT NULL,
    param_value VARCHAR(255),

    PRIMARY KEY (config_id, param_id),
    FOREIGN KEY (config_id) REFERENCES config(config_id)

    -- TODO: Enable when we pre-populate the `param_type` table:
    -- FOREIGN KEY (param_id) REFERENCES param_type(param_id)
);

-- Values of additional non-tunable parameters of the trial,
-- e.g., scheduled execution time, VM name / location, number of repeats, etc.
CREATE TABLE trial_param (
    exp_id VARCHAR(255) NOT NULL,
    trial_id INTEGER NOT NULL,
    param_id VARCHAR(255) NOT NULL,
    param_value VARCHAR(255),

    PRIMARY KEY (exp_id, trial_id, param_id),
    FOREIGN KEY (exp_id, trial_id) REFERENCES trial(exp_id, trial_id)

    -- TODO: Enable when we pre-populate the `param_type` table:
    -- FOREIGN KEY (param_id) REFERENCES param_type(param_id)
);

CREATE TABLE trial_result (
    exp_id VARCHAR(255) NOT NULL,
    trial_id INTEGER NOT NULL,
    metric_id VARCHAR(255) NOT NULL,
    metric_value VARCHAR(255),

    PRIMARY KEY (exp_id, trial_id, metric_id),
    FOREIGN KEY (exp_id, trial_id) REFERENCES trial(exp_id, trial_id)

    -- TODO: Enable when we pre-populate the `param_type` table:
    -- FOREIGN KEY (metric_id) REFERENCES param_type(param_id)
);

CREATE TABLE trial_telemetry (
    exp_id VARCHAR(255) NOT NULL,
    trial_id INTEGER NOT NULL,
    ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    metric_id VARCHAR(255) NOT NULL,
    metric_value VARCHAR(255),

    UNIQUE (exp_id, trial_id, ts, metric_id),
    FOREIGN KEY (exp_id, trial_id) REFERENCES trial(exp_id, trial_id)

    -- TODO: Enable when we pre-populate the `param_type` table:
    -- FOREIGN KEY (metric_id) REFERENCES param_type(param_id)
);

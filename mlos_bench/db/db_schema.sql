--
-- Copyright (c) Microsoft Corporation.
-- Licensed under the MIT License.
--
-- DB schema for storing MLOS benchmarking results.
-- The syntax works for SQLite3, DuckDB, PostgreSQL, and MySQL / MariaDB.

DROP TABLE IF EXISTS trial_telemetry;
DROP TABLE IF EXISTS trial_results;
DROP TABLE IF EXISTS trial_config;
DROP TABLE IF EXISTS experiment_merge;
DROP TABLE IF EXISTS trial_status;
DROP TABLE IF EXISTS experiment_config;
DROP TABLE IF EXISTS status_value;

-- Values and IDs should match the `mlos_bench.environment.Status` enum:
CREATE TABLE status_value (
    status_id INTEGER NOT NULL,
    status_name VARCHAR(16) NOT NULL,

    PRIMARY KEY (status_name),
    UNIQUE (status_id)
);

INSERT INTO status_value (status_id, status_name) VALUES
    (0, 'UNKNOWN'),
    (1, 'PENDING'),
    (2, 'READY'),
    (3, 'RUNNING'),
    (4, 'SUCCEEDED'),
    (5, 'CANCELED'),
    (6, 'FAILED'),
    (7, 'TIMED_OUT');

CREATE TABLE experiment_config (
    exp_id VARCHAR(255) NOT NULL,
    descr TEXT,
    git_repo VARCHAR(255) NOT NULL,
    git_commit VARCHAR(40) NOT NULL,

    PRIMARY KEY (exp_id)
);

CREATE TABLE trial_status (
    exp_id VARCHAR(255) NOT NULL,
    trial_id INTEGER NOT NULL,
    ts_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    ts_end TIMESTAMP,
    -- Should match the text IDs of `mlos_bench.environment.Status` enum:
    status VARCHAR(16) NOT NULL,

    PRIMARY KEY (exp_id, trial_id),
    FOREIGN KEY (exp_id) REFERENCES experiment_config(exp_id),
    FOREIGN KEY (status) REFERENCES status_value(status_name)
);

CREATE TABLE experiment_merge (
    dest_exp_id VARCHAR(255) NOT NULL,
    dest_trial_id INTEGER NOT NULL,
    source_exp_id VARCHAR(255) NOT NULL,
    source_trial_id INTEGER NOT NULL,

    UNIQUE (dest_exp_id, dest_trial_id, source_exp_id, source_trial_id),

    FOREIGN KEY (dest_exp_id, dest_trial_id)
        REFERENCES trial_status(exp_id, trial_id),

    FOREIGN KEY (source_exp_id, source_trial_id)
        REFERENCES trial_status(exp_id, trial_id)
);

CREATE TABLE trial_config (
    exp_id VARCHAR(255) NOT NULL,
    trial_id INTEGER NOT NULL,
    param_id VARCHAR(255) NOT NULL,
    param_value VARCHAR(255),

    PRIMARY KEY (exp_id, trial_id, param_id),
    FOREIGN KEY (exp_id, trial_id) REFERENCES trial_status(exp_id, trial_id),
    FOREIGN KEY (exp_id) REFERENCES experiment_config(exp_id)
);

CREATE TABLE trial_results (
    exp_id VARCHAR(255) NOT NULL,
    trial_id INTEGER NOT NULL,
    param_id VARCHAR(255) NOT NULL,
    param_value VARCHAR(255),

    PRIMARY KEY (exp_id, trial_id, param_id),
    FOREIGN KEY (exp_id, trial_id) REFERENCES trial_status(exp_id, trial_id),
    FOREIGN KEY (exp_id) REFERENCES experiment_config(exp_id)
);

CREATE TABLE trial_telemetry (
    exp_id VARCHAR(255) NOT NULL,
    trial_id INTEGER NOT NULL,
    ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    param_id VARCHAR(255) NOT NULL,
    param_value VARCHAR(255),

    UNIQUE (exp_id, trial_id, ts, param_id),
    FOREIGN KEY (exp_id, trial_id) REFERENCES trial_status(exp_id, trial_id),
    FOREIGN KEY (exp_id) REFERENCES experiment_config(exp_id)
);

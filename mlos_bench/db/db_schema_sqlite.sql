--
-- Copyright (c) Microsoft Corporation.
-- Licensed under the MIT License.
--
-- SQLite3/DuckDB version of the DB schema.

DROP TABLE IF EXISTS trial_telemetry;
DROP TABLE IF EXISTS trial_results;
DROP TABLE IF EXISTS trial_config;
DROP TABLE IF EXISTS experiment_merge;
DROP TABLE IF EXISTS trial_status;
DROP TABLE IF EXISTS experiment_config;

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
    status VARCHAR(16),

    PRIMARY KEY (exp_id, trial_id),
    FOREIGN KEY (exp_id) REFERENCES experiment_config(exp_id)
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

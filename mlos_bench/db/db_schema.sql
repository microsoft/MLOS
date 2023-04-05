--
-- Copyright (c) Microsoft Corporation.
-- Licensed under the MIT License.
--
-- DB schema for storing MLOS benchmarking results.
-- The syntax works for SQLite3, DuckDB, PostgreSQL, and MySQL / MariaDB.

DROP TABLE IF EXISTS trial_telemetry;
DROP TABLE IF EXISTS trial_results;
DROP TABLE IF EXISTS trial_config;
DROP TABLE IF EXISTS tunable_params;
DROP TABLE IF EXISTS experiment_merge;
DROP TABLE IF EXISTS trial;
DROP TABLE IF EXISTS experiment;

CREATE TABLE experiment (
    exp_id VARCHAR(255) NOT NULL,
    descr TEXT,
    metric_id VARCHAR(255) NOT NULL,
    git_repo VARCHAR(255) NOT NULL,
    git_commit VARCHAR(40) NOT NULL,

    PRIMARY KEY (exp_id)
);

CREATE TABLE trial (
    exp_id VARCHAR(255) NOT NULL,
    trial_id INTEGER NOT NULL,
    ts_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    ts_end TIMESTAMP,
    -- Should match the text IDs of `mlos_bench.environment.Status` enum:
    status VARCHAR(16) NOT NULL,

    PRIMARY KEY (exp_id, trial_id),
    FOREIGN KEY (exp_id) REFERENCES experiment(exp_id)
);

CREATE TABLE experiment_merge (
    dest_exp_id VARCHAR(255) NOT NULL,
    dest_trial_id INTEGER NOT NULL,
    source_exp_id VARCHAR(255) NOT NULL,
    source_trial_id INTEGER NOT NULL,

    UNIQUE (dest_exp_id, dest_trial_id, source_exp_id, source_trial_id),

    FOREIGN KEY (dest_exp_id, dest_trial_id)
        REFERENCES trial(exp_id, trial_id),

    FOREIGN KEY (source_exp_id, source_trial_id)
        REFERENCES trial(exp_id, trial_id)
);

-- Tunable parameters and their types, used for merging the data from several experiments.
-- Records in this table must match the `mlos_bench.tunables.Tunable` class.
CREATE TABLE tunable_params (
    param_id VARCHAR(255) NOT NULL,
    param_type VARCHAR(32) NOT NULL,  -- One of {int, float, categorical}
    param_default VARCHAR(255),
    param_meta VARCHAR(1023),  -- JSON-encoded metadata (range or categories).

    PRIMARY KEY (param_id)
);

CREATE TABLE trial_config (
    exp_id VARCHAR(255) NOT NULL,
    trial_id INTEGER NOT NULL,
    param_id VARCHAR(255) NOT NULL,
    param_value VARCHAR(255),

    PRIMARY KEY (exp_id, trial_id, param_id),
    -- TODO: Enable when we pre-populate the `tunable_params` table:
    -- FOREIGN KEY (param_id) REFERENCES tunable_params(param_id),
    FOREIGN KEY (exp_id, trial_id) REFERENCES trial(exp_id, trial_id),
    FOREIGN KEY (exp_id) REFERENCES experiment(exp_id)
);

CREATE TABLE trial_results (
    exp_id VARCHAR(255) NOT NULL,
    trial_id INTEGER NOT NULL,
    metric_id VARCHAR(255) NOT NULL,
    metric_value VARCHAR(255),

    PRIMARY KEY (exp_id, trial_id, metric_id),
    FOREIGN KEY (exp_id, trial_id) REFERENCES trial(exp_id, trial_id),
    FOREIGN KEY (exp_id) REFERENCES experiment(exp_id)
);

CREATE TABLE trial_telemetry (
    exp_id VARCHAR(255) NOT NULL,
    trial_id INTEGER NOT NULL,
    ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    metric_id VARCHAR(255) NOT NULL,
    metric_value VARCHAR(255),

    UNIQUE (exp_id, trial_id, ts, metric_id),
    FOREIGN KEY (exp_id, trial_id) REFERENCES trial(exp_id, trial_id),
    FOREIGN KEY (exp_id) REFERENCES experiment(exp_id)
);

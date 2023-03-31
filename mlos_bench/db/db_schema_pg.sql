--
-- Copyright (c) Microsoft Corporation.
-- Licensed under the MIT License.
--
-- PostgreSQL version of the DB schema.

DROP TABLE IF EXISTS experiment_config CASCADE;
DROP TABLE IF EXISTS experiment_merge CASCADE;
DROP TABLE IF EXISTS trial_status CASCADE;
DROP TABLE IF EXISTS trial_config CASCADE;
DROP TABLE IF EXISTS trial_results CASCADE;
DROP TABLE IF EXISTS trial_telemetry CASCADE;

DROP TYPE IF EXISTS experiment_id_t CASCADE;
DROP TYPE IF EXISTS trial_id_t CASCADE;
DROP TYPE IF EXISTS param_id_t CASCADE;
DROP TYPE IF EXISTS param_value_t CASCADE;
DROP TYPE IF EXISTS status_t CASCADE;

CREATE DOMAIN experiment_id_t AS VARCHAR(255) NOT NULL;
CREATE DOMAIN trial_id_t AS INTEGER NOT NULL;
CREATE DOMAIN param_id_t AS VARCHAR(255) NOT NULL;
CREATE DOMAIN param_value_t AS VARCHAR(255);

-- Should match the `mlos_bench.environment.Status` enum.
CREATE TYPE status_t AS ENUM (
    'UNKNOWN',
    'PENDING',
    'READY',
    'RUNNING',
    'SUCCEEDED',
    'CANCELED',
    'FAILED',
    'TIMED_OUT'
);

CREATE TABLE experiment_config (
    exp_id experiment_id_t,
    descr TEXT,
    git_repo VARCHAR(255) NOT NULL,
    git_commit VARCHAR(40) NOT NULL,

    PRIMARY KEY (exp_id)
);

CREATE SEQUENCE trial_id_seq;

CREATE TABLE trial_status (
    exp_id experiment_id_t,
    trial_id trial_id_t DEFAULT nextval('trial_id_seq'),
    ts_start TIMESTAMP NOT NULL DEFAULT now(),
    ts_end TIMESTAMP,
    status status_t,

    PRIMARY KEY (exp_id, trial_id),
    FOREIGN KEY (exp_id) REFERENCES experiment_config(exp_id)
);

ALTER SEQUENCE trial_id_seq OWNED BY trial_status.trial_id;

CREATE TABLE experiment_merge (
    dest_exp_id experiment_id_t,
    dest_trial_id trial_id_t,
    source_exp_id experiment_id_t,
    source_trial_id trial_id_t,

    UNIQUE (dest_exp_id, dest_trial_id, source_exp_id, source_trial_id),

    FOREIGN KEY (dest_exp_id, dest_trial_id)
        REFERENCES trial_status(exp_id, trial_id),

    FOREIGN KEY (source_exp_id, source_trial_id)
        REFERENCES trial_status(exp_id, trial_id)
);

CREATE TABLE trial_config (
    exp_id experiment_id_t,
    trial_id trial_id_t,
    param_id param_id_t,
    param_value param_value_t,

    PRIMARY KEY (exp_id, trial_id, param_id),
    FOREIGN KEY (exp_id, trial_id) REFERENCES trial_status(exp_id, trial_id),
    FOREIGN KEY (exp_id) REFERENCES experiment_config(exp_id)
);

CREATE TABLE trial_results (
    exp_id experiment_id_t,
    trial_id trial_id_t,
    param_id param_id_t,
    param_value param_value_t,

    PRIMARY KEY (exp_id, trial_id, param_id),
    FOREIGN KEY (exp_id, trial_id) REFERENCES trial_status(exp_id, trial_id),
    FOREIGN KEY (exp_id) REFERENCES experiment_config(exp_id)
);

CREATE TABLE trial_telemetry (
    exp_id experiment_id_t,
    trial_id trial_id_t,
    ts TIMESTAMP NOT NULL DEFAULT now(),
    param_id param_id_t,
    param_value param_value_t,

    UNIQUE (exp_id, trial_id, ts, param_id),
    FOREIGN KEY (exp_id, trial_id) REFERENCES trial_status(exp_id, trial_id),
    FOREIGN KEY (exp_id) REFERENCES experiment_config(exp_id)
);

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
DROP TYPE IF EXISTS status_t CASCADE;

CREATE DOMAIN experiment_id_t AS varchar(128) NOT NULL;
CREATE DOMAIN trial_id_t AS integer NOT NULL;
CREATE DOMAIN param_id_t AS varchar(256) NOT NULL;

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
    descr text,
    git_repo varchar(255) NOT NULL,
    git_commit varchar(40) NOT NULL,

    PRIMARY KEY (exp_id)
);

CREATE SEQUENCE trial_id_seq;

CREATE TABLE trial_status (
    exp_id experiment_id_t,
    trial_id trial_id_t DEFAULT nextval('trial_id_seq'),
    ts_start timestamp NOT NULL DEFAULT now(),
    ts_end timestamp,
    status status_t,

    PRIMARY KEY (exp_id, trial_id),
    FOREIGN KEY (exp_id) REFERENCES experiment_config(exp_id)
);

ALTER SEQUENCE trial_id_seq owned by trial_status.trial_id;

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
    param_value varchar(255),

    PRIMARY KEY (exp_id, trial_id, param_id),
    FOREIGN KEY (exp_id, trial_id) REFERENCES trial_status(exp_id, trial_id),
    FOREIGN KEY (exp_id) REFERENCES experiment_config(exp_id)
);

CREATE TABLE trial_results (
    exp_id experiment_id_t,
    trial_id trial_id_t,
    param_id param_id_t,
    param_value varchar(255),

    PRIMARY KEY (exp_id, trial_id, param_id),
    FOREIGN KEY (exp_id, trial_id) REFERENCES trial_status(exp_id, trial_id),
    FOREIGN KEY (exp_id) REFERENCES experiment_config(exp_id)
);

CREATE TABLE trial_telemetry (
    exp_id experiment_id_t,
    trial_id trial_id_t,
    ts timestamp NOT NULL DEFAULT now(),
    param_id param_id_t,
    param_value varchar(255),

    UNIQUE (exp_id, trial_id, ts, param_id),
    FOREIGN KEY (exp_id, trial_id) REFERENCES trial_status(exp_id, trial_id),
    FOREIGN KEY (exp_id) REFERENCES experiment_config(exp_id)
);

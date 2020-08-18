-- Copyright (c) Microsoft Corporation.
-- Licensed under the MIT License.

IF NOT EXISTS
(
	SELECT name FROM dbo.sysdatabases
	WHERE name = 'MlosModels'
)
CREATE DATABASE MlosModels;
GO

USE MlosModels;

-- DROP TABLE SimpleModels;
CREATE TABLE SimpleModels (
	model_id UNIQUEIDENTIFIER DEFAULT NEWID() PRIMARY KEY,
	model_type TEXT NOT NULL,
	model_hypergrid TEXT NOT NULL,
	model_config TEXT NOT NULL,
	max_version INT DEFAULT 0
);

-- DROP TABLE SerializedModels;
CREATE TABLE SerializedModels (
	model_id UNIQUEIDENTIFIER FOREIGN KEY REFERENCES SimpleModels(model_id),
	model_version INT,
	serialized_model TEXT
);

-- DROP TABLE Optimizers;
CREATE TABLE Optimizers (
	optimizer_id UNIQUEIDENTIFIER DEFAULT NEWID() PRIMARY KEY,
	optimizer_type VARCHAR(255) NOT NULL,
	optimizer_config TEXT,
	optimizer_hypergrid TEXT DEFAULT NULL,
	optimizer_focused_hypergrid TEXT DEFAULT NULL,
	optimization_problem TEXT DEFAULT NULL, -- TODO: move to a separate table and reference a problem instance here.
	registered_parameter_combos TEXT DEFAULT NULL
);


-- DROP TABLE OptimizerSimpleModelsRelation;
CREATE TABLE OptimizerSimpleModelsRelation (
	optimizer_id UNIQUEIDENTIFIER FOREIGN KEY REFERENCES Optimizers(optimizer_id),
	model_id UNIQUEIDENTIFIER FOREIGN KEY REFERENCES SimpleModels(model_id)
);


-- DROP TABLE RemoteProcedureCalls;
CREATE TABLE RemoteProcedureCalls (
	request_id UNIQUEIDENTIFIER DEFAULT NEWID() PRIMARY KEY, -- rpc request id
	request_submission_time DATETIME DEFAULT GETUTCDATE(),
	request_status varchar(16) NOT NULL DEFAULT 'submitted',
	remote_procedure_name varchar(255) NOT NULL,
	execution_context TEXT,
	arguments TEXT,
	result TEXT,
	timeout_dt DATETIME2 DEFAULT NULL,
	CONSTRAINT check_status CHECK (
		request_status IN (
			'submitted',
			'in progress',
			'complete',
			'failed',
			'cancelled',
			'aborted',
			'timed out'
		)
	)
);

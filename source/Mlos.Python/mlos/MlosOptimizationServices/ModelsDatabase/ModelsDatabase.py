#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
import os

from mlos.Logger import create_logger
from .DatabaseConnector import DatabaseConnector, connection_required
from .Relations import RemoteProcedureCall, Optimizer, SimpleModel



class ModelsDatabase:
    """ This class constitutes the entire and only interface to the Models Database.

    """

    @classmethod
    def connect_to_endpoint(cls, credentials):
        models_database = ModelsDatabase(connection_string=credentials)
        return models_database

    def __init__(self, connection_string, logger=None):
        self.logger = logger if logger is not None else create_logger("ModelsDatabase")
        self.connection_string = connection_string
        self.database_connector = DatabaseConnector(
            connection_string=connection_string,
            logger=self.logger
        )

    @property
    def connection(self):
        return self.database_connector.connection

    @property
    def connected(self):
        return self.database_connector.connected

    def connect(self, use_default_database=False, autocommit=False):
        return self.database_connector.connect(use_default_database=use_default_database, autocommit=autocommit)

    def disconnect(self):
        return self.database_connector.disconnect()



########################################################################################################################
#
#                                                QUERY HELPERS
#
########################################################################################################################

    def _select(self, query_text, rethrow=True, error_message="Failed to execute a select statement."):
        all_rows = []
        try:
            cursor = self.connection.cursor()
            cursor.execute(query_text)
            all_rows = cursor.fetchall()
        except:
            self.logger.error(error_message, exc_info=True)
            self.connection.rollback()
            if rethrow:
                raise
        finally:
            cursor.close()

        return all_rows

    def _update(self, sql_text, rethrow=True, error_message="Failed to execute update statement.", returning=False, commit=True):
        all_rows = []
        try:
            cursor = self.connection.cursor()
            cursor.execute(sql_text)
            if returning:
                all_rows = cursor.fetchall()
            if commit:
                self.connection.commit()
        except:
            self.logger.error(error_message, exc_info=True)
            self.connection.rollback()
            if rethrow:
                raise
        finally:
            cursor.close()

        return all_rows

    def _insert(self, sql_text, rethrow=True, error_message="Failed to execute insert statement", returning=False, commit=True):
        return self._update(sql_text, rethrow, error_message, returning, commit)

########################################################################################################################
#
#                                                INITIALIZE DATABASE
#
########################################################################################################################

    @connection_required(use_default_database=True, autocommit=True)
    def drop_target_database(self):
        self.logger.info("Dropping target database.")
        cursor = self.connection.cursor()
        cursor.execute(f"DROP DATABASE IF EXISTS {self.connection_string.database_name};")  # TODO: sql injection...
        self.connection.commit()
        cursor.close()

    @connection_required(use_default_database=True, autocommit=True)
    def create_target_database(self):
        self.logger.info("Creating target database.")
        cursor = self.connection.cursor()
        cursor.execute(f"CREATE DATABASE {self.connection_string.database_name};")  # TODO: sql injection
        self.connection.commit()
        cursor.close()

    @connection_required(use_default_database=True, autocommit=True)
    def create_database_schema(self):
        self.logger.info("Creating target database schema.")
        schema_file_path = os.path.join(os.getcwd(), "MlosOptimizationServices", "ModelsDatabase", "SQLScripts", "Schema.sql")
        with open(schema_file_path, 'r') as in_file:
            # The usage of 'GO' trips up pyodbc, but we need it in sqlcmd in the container.
            # let's filter it out
            schema_script = "\n".join([line.strip() for line in in_file if line.strip() != 'GO'])

        cursor = self.connection.cursor()
        cursor.execute(schema_script)
        self.connection.commit()
        cursor.close()


########################################################################################################################
#
#                                                Models Database Interface - Runtime Portion
#
########################################################################################################################

    @connection_required()
    def submit_remote_procedure_call(self, rpc: RemoteProcedureCall) -> RemoteProcedureCall:
        sql = f'''
            INSERT INTO RemoteProcedureCalls (
                remote_procedure_name,
                execution_context,
                arguments
            )
            OUTPUT Inserted.request_id, Inserted.request_status
            VALUES (
                '{rpc.remote_procedure_name}',
                '{rpc.execution_context}',
                '{rpc.arguments}'
            )
        '''
        all_rows = self._insert(
            sql_text=sql,
            returning=True,
            error_message="Failed to submit a remote procedure call request"
        )
        only_row = all_rows[0]
        rpc.request_id = only_row[0]
        rpc.request_status = only_row[1]

        return rpc

    @connection_required()
    def get_updated_request_status(self, rpc):
        # TODO: incorporate expected_status
        sql = f"SELECT request_status, result FROM RemoteProcedureCalls WHERE request_id = '{rpc.request_id}'"
        all_rows = self._select(query_text=sql, error_message="Failed to check request status.")
        only_row = all_rows[0]
        rpc.request_status = only_row[0]
        rpc.result = only_row[1]
        return rpc



    @connection_required()
    def get_submitted_remote_procedure_calls(self):
        sql = '''
            SELECT
                request_id, 
                request_status,
                remote_procedure_name,
                arguments
            FROM
                RemoteProcedureCalls
            WHERE
                request_status = 'submitted'
        '''
        all_rows = self._select(query_text=sql)
        all_rpcs = []
        for row in all_rows:
            rpc = {
                "request_id": row[0],
                "request_status": row[1],
                "remote_procedure_name": row[2],
                "arguments": row[3]
            }
            all_rpcs.append(rpc)
        return all_rpcs

    @connection_required()
    def get_rpc_to_complete(self, allowed_rpc_names):

        self.time_out_expired_rpcs()

        sql = f'''
            WITH OutstandingRpcId AS (
                SELECT TOP 1 
                    request_id
                FROM 
                    RemoteProcedureCalls
                WHERE 
                    request_status = 'submitted'
                    AND
                    remote_procedure_name in ({",".join("'" + name + "'" for name in allowed_rpc_names)})
                ORDER BY
                    request_submission_time asc
            )
            UPDATE RemoteProcedureCalls
            SET
                request_status = 'in progress'
            OUTPUT 
                inserted.request_id,
                inserted.remote_procedure_name,
                inserted.execution_context,
                inserted.arguments
            WHERE
                request_id IN (SELECT request_id FROM OutstandingRpcId)
        '''
        all_rows = self._update(
            sql_text=sql,
            rethrow=True,
            error_message="Failed to get an outstanding rpc to complete.",
            returning=True,
            commit=True
        )

        if not all_rows:
            return None

        only_row = all_rows[0]
        rpc_object = RemoteProcedureCall(
            request_id=only_row[0],
            remote_procedure_name=only_row[1],
            execution_context=only_row[2],
            arguments=only_row[3]
        )
        self.logger.info(f"Got an rpc to complete. Request ID: {rpc_object.request_id}, remote procedure name: {rpc_object.remote_procedure_name}")
        return rpc_object

    @connection_required()
    def complete_rpc(self, rpc_object):
        sql = f'''
            UPDATE RemoteProcedureCalls
            SET 
                request_status = '{rpc_object.request_status}',
                result = {'NULL' if rpc_object.result is None else "'" + rpc_object.result + "'"}
            WHERE
                request_id = '{rpc_object.request_id}'
                AND
                (timeout_dt IS NULL OR timeout_dt < GETUTCDATE())
                AND
                request_status = 'in progress'
        '''
        self._update(
            sql_text=sql,
            rethrow=True,
            error_message=f"Failed to complete rpc {rpc_object.request_id}",
            returning=False,
            commit=True
        )
        self.logger.info(f"Completed rpc {rpc_object.request_id}")


    @connection_required()
    def update_rpc_request_status(self, rpc_object):
        sql = f'''
            UPDATE RemoteProcedureCalls
            SET
                request_status = '{rpc_object.request_status}'
            OUTPUT
                Deleted.request_status,
                Inserted.request_status
            WHERE
                request_id = '{rpc_object.request_id}'
                AND
                request_status = '{rpc_object.expected_current_status}'
        '''
        all_rows = self._update(
            sql_text=sql,
            returning=True
        )
        if not all_rows:
            raise RuntimeError("TODO: get the newest status and have the callers handle this case")

        only_row = all_rows[0]
        old_status = only_row[0]
        new_status = only_row[1]

        if old_status == rpc_object.expected_current_status and new_status == rpc_object.request_status:
            rpc_object.expected_current_status = new_status
            rpc_object.request_status = new_status

        return rpc_object

    @connection_required()
    def remove_rpc(self, rpc_object: RemoteProcedureCall):
        sql = f"DELETE FROM RemoteProcedureCalls WHERE request_id = '{rpc_object.request_id}'"
        self._update(sql_text=sql, error_message=f"Failed to delete rpc {rpc_object.request_id}")


    @connection_required()
    def time_out_expired_rpcs(self):
        sql = '''
            UPDATE
                RemoteProcedureCalls
            SET
                request_status = 'timed out'
            WHERE
                request_status = 'submitted'
                AND
                timeout_dt < GETUTCDATE()
        '''
        self._update(sql_text=sql, error_message="Failed to time out expired rpcs.")


########################################################################################################################
#
#                                                Models Database Interface - Optimizers and Models Portion
#
########################################################################################################################

    @connection_required()
    def create_optimizer(self, optimizer: Optimizer) -> Optimizer:
        sql = f'''
            INSERT INTO Optimizers (
                optimizer_type, 
                optimizer_config,
                optimizer_hypergrid,
                optimizer_focused_hypergrid,
                optimization_problem
            )
            OUTPUT Inserted.optimizer_id
            VALUES (
                '{optimizer.optimizer_type}',
                '{optimizer.optimizer_config}',
                '{optimizer.optimizer_hypergrid}',
                {"'" + optimizer.optimizer_focused_hypergrid + "'" if optimizer.optimizer_focused_hypergrid is not None else 'NULL'},
                {"'" + optimizer.optimization_problem + "'" if optimizer.optimization_problem is not None else 'NULL'}
            )
        '''
        all_rows = self._insert(
            sql_text=sql,
            returning=True,
            error_message="Failed to insert new optimizer."
        )

        only_row = all_rows[0]
        optimizer.optimizer_id = only_row[0]
        return optimizer

    @connection_required()
    def update_optimizer_config(self, optimizer: Optimizer) -> None:
        sql = f'''
        UPDATE Optimizers
        SET optimizer_config = '{optimizer.optimizer_config}'
        WHERE optimizer_id = '{optimizer.optimizer_id}'
        '''
        self._update(
            sql_text=sql,
            error_message="Failed to update optimizer config."
        )

    @connection_required()
    def persist_models(self, optimizer: Optimizer) -> Optimizer:
        """ Persists the optimizers serialized models into the database.

        The idea is that whenever when an optimizer has updated a model state, we want to put that newly updated
        model into the database.

        If the model already has an id, we only insert the serialized model into the SerializedModels table,
        we update the optimizer.model_version.

        If the model does not have an id, it means it is a brand new model. We first put its metadata in the
        SimpleModels table, thus receiving an id. We link the model to optimizer in the OptimizersSimpleModelsRelation.
        We then persist the serialized model in the SimpleModels table.

        :param optimizer:
        :return:
        """
        for simple_model in optimizer.models:
            if simple_model.model_id is None:
                simple_model = self.create_simple_model(simple_model)
            self.persist_simple_model_version(simple_model)

        return optimizer

    @connection_required()
    def create_simple_model(self, simple_model: SimpleModel) -> SimpleModel:
        """ Creates a new instance of the simple model in the database.

        :param simple_model:
        :return:
        """

        # TODO: make sure the model does not already exist.

        sql = f'''
            BEGIN TRANSACTION
                SET NOCOUNT ON;
                DECLARE @ModelId TABLE (model_id UNIQUEIDENTIFIER);
                
                INSERT INTO SimpleModels(model_type, model_hypergrid, model_config)
                OUTPUT Inserted.model_id INTO @ModelId(model_id)
                VALUES('{simple_model.model_type}', '{simple_model.model_hypergrid}', '{simple_model.model_config}');
            
                INSERT INTO OptimizerSimpleModelsRelation(optimizer_id, model_id)
                OUTPUT Inserted.model_id
                SELECT '{simple_model.optimizer_id}', model_id FROM @ModelId;

            COMMIT
        '''
        all_rows = self._insert(
            sql_text=sql,
            returning=True,
            error_message="Failed to create new simple model.",
            rethrow=True
        )
        if not all_rows:
            self.logger.error("Failed to create new simple model.")
            raise RuntimeError("Failed to create new simple model.")

        only_row = all_rows[0]
        model_id = only_row[0]
        simple_model.model_id = model_id
        return simple_model


    @connection_required()
    def persist_simple_model_version(self, simple_model: SimpleModel) -> SimpleModel:
        """ Persists a version of the simple model into the SerializedModels table.

        :param simple_model:
        :return:
        """
        sql = f'''
            BEGIN TRANSACTION
                INSERT INTO SerializedModels (model_id, model_version, serialized_model)
                VALUES (
                    '{simple_model.model_id}',
                    {simple_model.model_version},
                    '{simple_model.serialized_model}'
                );

                UPDATE SimpleModels
                SET max_version = {simple_model.model_version}
                WHERE model_id = '{simple_model.model_id}';
            COMMIT;
        '''
        self._insert(
            sql_text=sql,
            error_message=f"Failed to persist model version {simple_model.model_version} for model id: {simple_model.model_id}",
            returning=False,
            rethrow=True
        )

        return simple_model





    @connection_required()
    def get_optimizer_state(self, optimizer: Optimizer) -> Optimizer:
        """ Retruns all of the optimizers state that is required to instantiate it in memory.

        The Optimizer object contains the optimizer_id and optimizer_type, it might also contain model version.
        We use this information to populate:
        * optimizer_config
        * optimizer_hypergrid
        * optimizer_focused_hypergrid (?)
        * serialized_model (?)
        * model_version (?)

        (?) - these fields are populated conditionally.

        Specifically, an optimzier might not have a focused_hypergrid.

        If model_version was already specified, we will attempt to fetch that version from the database.
        If model_version was not specified, we will fetch the newest version of the model and populate
        the model_version.
        If serialized_model doesn't exist in the database, it will remain None in the optimizer object - this means
        that the model has not been trained on anything yet, so it has no state worth storing.

        :param optimizer:
        :return:
        """
        if not optimizer.models:
            optimizer.models = [SimpleModel()]

        simple_model = optimizer.models[0]

        if simple_model.model_version not in (0, None):
            model_version_predicate = f"SerializedModels.model_version = {optimizer.models[0].model_version} AND "
        else:
            model_version_predicate = ''

        # TODO: handle the case when optimizer has more than one model
        sql = f'''
            SELECT TOP 1
                Optimizers.optimizer_config,
                Optimizers.optimizer_hypergrid,
                Optimizers.optimizer_focused_hypergrid,
                Optimizers.optimization_problem,
                Optimizers.registered_parameter_combos,
                SimpleModels.model_id,
                SimpleModels.model_type,
                SimpleModels.model_hypergrid,
                SerializedModels.model_version,
                SerializedModels.serialized_model
            FROM 
                Optimizers
                JOIN OptimizerSimpleModelsRelation ON Optimizers.optimizer_id = OptimizerSimpleModelsRelation.optimizer_id
                JOIN SimpleModels ON SimpleModels.model_id = OptimizerSimpleModelsRelation.model_id
                JOIN SerializedModels ON SerializedModels.model_id = OptimizerSimpleModelsRelation.model_id
            WHERE
                {model_version_predicate}
                Optimizers.optimizer_id = '{optimizer.optimizer_id}'
            ORDER BY SerializedModels.model_version DESC
        '''

        all_rows = self._select(query_text=sql, error_message="Failed to get optimizer state.")
        if all_rows:
            only_row = all_rows[0]
            optimizer.optimizer_config = only_row[0]
            optimizer.optimizer_hypergrid = only_row[1]
            optimizer.optimizer_focused_hypergrid = only_row[2]
            optimizer.optimization_problem = only_row[3]
            optimizer.registered_params_combos = only_row[4]
            simple_model.model_id = only_row[5]
            simple_model.model_type = only_row[6]
            simple_model.model_hypergrid = only_row[7]
            simple_model.model_version = only_row[8]
            simple_model.serialized_model = only_row[9]
            return optimizer

        # If we got here, means we got zero rows, which is the case for models that don't yet exist.
        sql = f'''
            SELECT
                Optimizers.optimizer_config,
                Optimizers.optimizer_hypergrid,
                Optimizers.optimizer_focused_hypergrid,
                Optimizers.optimization_problem
            FROM 
                Optimizers
            WHERE
                optimizer_id = '{optimizer.optimizer_id}'
        '''
        all_rows = self._select(query_text=sql, error_message="Failed to get optimizer state.")
        if all_rows:
            only_row = all_rows[0]
            optimizer.optimizer_config = only_row[0]
            optimizer.optimizer_hypergrid = only_row[1]
            optimizer.optimizer_focused_hypergrid = only_row[2]
            optimizer.optimization_problem = only_row[3]
            return optimizer

        raise RuntimeError("TODO: figure out what to do if we get here")


    @connection_required()
    def persist_registered_parameter_combos(self, optimizer: Optimizer) -> Optimizer:
        sql = f'''
            UPDATE Optimizers
            SET registered_parameter_combos = '{optimizer.registered_params_combos}'
            WHERE optimizer_id = '{optimizer.optimizer_id}'
        '''
        self._update(sql_text=sql, rethrow=False)
        return optimizer

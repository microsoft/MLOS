// -----------------------------------------------------------------------
// <copyright file="ModelsDatabase.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Data.SqlClient;

using Mlos.Model.Services.ModelsDb.ObjectRelationalMappings;

namespace Mlos.Model.Services.ModelsDb
{
    public class ModelsDatabase
    {
        private readonly ModelsDatabaseConnectionDetails connectionDetails;

        public ModelsDatabase(string connectionDetailsJsonFilePath)
        {
            if (connectionDetailsJsonFilePath != null)
            {
                connectionDetails = ModelsDatabaseConnectionDetails.FromJsonFile(connectionDetailsJsonFilePath);
            }
        }

        /// <summary>
        /// Creates a new optimizer record in the ModelsDatabase.
        /// </summary>
        /// <param name="optimizer">Optimizer object containing its configuration and search space.
        /// some worker can instantiate this type of model and that the configuration is valid.
        /// </param>
        /// <returns></returns>
        public Optimizer CreateNewOptimizer(Optimizer optimizer)
        {
            if (connectionDetails == null)
            {
                return null;
            }

            using var commandWrapper = new ModelsDatabaseCommandWrapper(connectionDetails.ConnectionString);
            var sqlCommand = commandWrapper.Command;
            sqlCommand.CommandText =
                    "INSERT INTO Optimizers(optimizer_type, optimization_problem) " +
                    "OUTPUT Inserted.optimizer_id " +
                    "VALUES(@optimizerType, @optimizationProblem)";

            string optimizerType = Enum.GetName(typeof(Optimizer.RemoteOptimizerType), optimizer.OptimizerType);
            sqlCommand.Parameters.Add(new SqlParameter("@optimizerType", System.Data.SqlDbType.Text, optimizerType.Length)).Value = optimizerType;
            sqlCommand.Parameters.Add(new SqlParameter("@optimizationProblem", System.Data.SqlDbType.Text, optimizer.OptimizationProblemJsonString.Length)).Value = optimizer.OptimizationProblemJsonString;
            sqlCommand.Prepare();

            using var dataReader = sqlCommand.ExecuteReader();
            dataReader.Read();
            optimizer.OptimizerId = (Guid)dataReader.GetValue(0);

            return optimizer;
        }

        public RemoteProcedureCall SubmitRemoteProcedureCallRequest(RemoteProcedureCall remoteProcedureCall)
        {
            using var commandWrapper = new ModelsDatabaseCommandWrapper(connectionDetails.ConnectionString);

            var sqlCommand = commandWrapper.Command;
            sqlCommand.CommandText =
                "INSERT INTO RemoteProcedureCalls (remote_procedure_name, execution_context, arguments) " +
                "OUTPUT Inserted.request_id, Inserted.request_status " +
                "VALUES (@remoteProcedureName, @executionContext, @arguments)";
            sqlCommand.Parameters.Add(new SqlParameter("@remoteProcedureName", System.Data.SqlDbType.Text, remoteProcedureCall.RemoteProcedureName.Length)).Value = remoteProcedureCall.RemoteProcedureName;
            sqlCommand.Parameters.Add(new SqlParameter("@executionContext", System.Data.SqlDbType.Text, remoteProcedureCall.ExecutionContextJsonString.Length)).Value = remoteProcedureCall.ExecutionContextJsonString;
            sqlCommand.Parameters.Add(new SqlParameter("@arguments", System.Data.SqlDbType.Text, remoteProcedureCall.ArgumentsJsonString.Length)).Value = remoteProcedureCall.ArgumentsJsonString;
            sqlCommand.Prepare();

            var dataReader = sqlCommand.ExecuteReader();
            dataReader.Read();

            remoteProcedureCall.RequestId = (Guid)dataReader.GetValue(0);
            string statusString = (string)dataReader.GetValue(1);
            remoteProcedureCall.SetStatus(statusString);

            return remoteProcedureCall;
        }

        public RemoteProcedureCall GetUpdatedRPCRequestStatus(RemoteProcedureCall remoteProcedureCall)
        {
            using var commandWrapper = new ModelsDatabaseCommandWrapper(connectionDetails.ConnectionString);

            var sqlCommand = commandWrapper.Command;

            // TODO: add the timeout. Also add a timeout to connection open.
            //
            sqlCommand.CommandText = "SELECT request_status, result FROM RemoteProcedureCalls WHERE request_id = @requestId";
            sqlCommand.Parameters.Add(new SqlParameter("@requestId", System.Data.SqlDbType.UniqueIdentifier)).Value = remoteProcedureCall.RequestId;
            sqlCommand.Prepare();

            using var dataReader = sqlCommand.ExecuteReader();
            dataReader.Read();
            remoteProcedureCall.SetStatus((string)dataReader.GetValue(0));
            if (!dataReader.IsDBNull(1))
            {
                remoteProcedureCall.ResultJsonString = (string)dataReader.GetValue(1);
            }

            return remoteProcedureCall;
        }
    }
}

// -----------------------------------------------------------------------
// <copyright file="SimpleBayesianOptimizerProxy.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Collections.Generic;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading;
using Mlos.Core;
using Mlos.Model.Services.Client.Proxies;
using Mlos.Model.Services.ModelsDb;
using Mlos.Model.Services.ModelsDb.ObjectRelationalMappings;
using Mlos.Model.Services.Spaces;

namespace Mlos.Model.Services.Client.Proxies
{
    public class ArgumentsToSuggest
    {
        [JsonPropertyName("random")]
        public bool Random { get; set; }
    }

    /// <summary>
    /// A proxy to a SimpleBayesianOptimizer executing within the Mlos.Model.Services.
    /// </summary>
    public class SimpleBayesianOptimizerProxy : ISimpleBayesianOptimizerProxy
    {
        private readonly ModelsDatabase modelsDatabase;
        private readonly OptimizationProblem optimizationProblem;
        private SimpleBayesianOptimizerExecutionContext optimizerExecutionContext;
        public Guid? OptimizerId { get; set; }

        public SimpleBayesianOptimizerExecutionContext OptimizerExecutionContext
        {
            get
            {
                return optimizerExecutionContext;
            }
        }

        public SimpleBayesianOptimizerProxy(ModelsDatabase modelsDatabase, OptimizationProblem optimizationProblem, Guid? optimizerId)
        {
            this.modelsDatabase = modelsDatabase;
            this.optimizationProblem = optimizationProblem;
            OptimizerId = optimizerId;
            optimizerExecutionContext = new SimpleBayesianOptimizerExecutionContext()
            {
                OptimizerId = optimizerId,
            };
            optimizerExecutionContext.ModelVersions.Add(0);
        }

        /// <summary>
        /// Suggests a set of parameters to try.
        ///
        /// Specifically, it submits a remote procedure call request for a remote optimizer to suggest a set of parameters to try.
        /// It then waits for that rpc to complete and returns the result.
        ///
        /// </summary>
        /// <param name="random"></param>
        /// <returns>JSON string with the result. TODO: make it a generic to return a config belonging to a given search space.</returns>
        public string Suggest(bool random = false)
        {
            var arguments = new ArgumentsToSuggest { Random = random };

            RemoteProcedureCall rpcRequest = new RemoteProcedureCall(
                remoteProcedureName: "DistributableSimpleBayesianOptimizer.suggest",
                executionContextJsonString: JsonSerializer.Serialize(OptimizerExecutionContext),
                argumentsJsonString: JsonSerializer.Serialize(arguments));

            InvokeRemoteProcedureCall(rpcRequest);
            return rpcRequest.ResultJsonString;
        }

        /// <summary>
        /// Registers a (config, target) tuple with the optimizer.
        /// </summary>
        /// <param name="paramsJsonString"></param>
        /// <param name="targetValue"></param>
        public void Register(string paramsJsonString, double targetValue)
        {
            string executionContextJsonString = $@"{{""optimizer_id"": ""{OptimizerId}"", ""model_versions"": [0]}}";
            string argumentsJsonString = $@"{{""params"": {paramsJsonString}, ""target_value"": {targetValue} }}";
            RemoteProcedureCall rpcRequest = new RemoteProcedureCall(
                remoteProcedureName: "DistributableSimpleBayesianOptimizer.register",
                executionContextJsonString: executionContextJsonString,
                argumentsJsonString: argumentsJsonString);

            InvokeRemoteProcedureCall(rpcRequest);
        }

        /// <summary>
        /// Asks the optimizer to predict the target value based on the parameters encoded in paramsJsonString.
        /// </summary>
        /// <param name="paramsJsonString"></param>
        /// <returns></returns>
        public string Predict(string paramsJsonString)
        {
            string executionContextJsonString = $@"{{""optimizer_id"": ""{OptimizerId}"", ""model_versions"": [0]}}";
            string argumentsJsonString = $@"{{""named_params"": {paramsJsonString}}}";
            RemoteProcedureCall rpcRequest = new RemoteProcedureCall(
                remoteProcedureName: "DistributableSimpleBayesianOptimizer.predict",
                executionContextJsonString: executionContextJsonString,
                argumentsJsonString: argumentsJsonString);

            InvokeRemoteProcedureCall(rpcRequest);

            // TODO: check rpc status
            //
            return rpcRequest.ResultJsonString;
        }

        /// <summary>
        /// Submits an RPC request and awaits its completion.
        /// TODO: move this to a separate class where it could be reused by other components.
        /// </summary>
        /// <param name="rpc"></param>
        /// <returns></returns>
        private RemoteProcedureCall InvokeRemoteProcedureCall(RemoteProcedureCall rpc)
        {
            TimeSpan spinInterval = TimeSpan.FromMilliseconds(10);    // Spin every 10ms. TODO: make it tunable.

            if (rpc.Status != RemoteProcedureCall.RPCStatus.None)
            {
                throw new ArgumentException("RPC status must be None before submission.");
            }

            modelsDatabase.SubmitRemoteProcedureCallRequest(remoteProcedureCall: rpc);

            // TODO: retries
            //
            if (rpc.Status != RemoteProcedureCall.RPCStatus.Submitted)
            {
                throw new SystemException("Failed to submit RPC"); // TODO: create own exception class for this.
            }

            RemoteProcedureCall.RPCStatus oldStatus = rpc.Status;

            while (true)
            {
                Thread.Sleep(spinInterval);
                modelsDatabase.GetUpdatedRPCRequestStatus(rpc);
                if (rpc.Status != oldStatus)
                {
                    // TODO: add dealing with timeouts
                    //
                    if (rpc.Status == RemoteProcedureCall.RPCStatus.InProgress)
                    {
                        continue;
                    }
                    else
                    {
                        return rpc;
                    }
                }
            }
        }
    }
}

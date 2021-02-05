// -----------------------------------------------------------------------
// <copyright file="ExperimentManagerService.cs" company="Microsoft Corporation">
// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root
// for license information.
// </copyright>
// -----------------------------------------------------------------------

using System;
using System.Threading.Tasks;

using Grpc.Core;
using Mlos.ExperimentService;

namespace Mlos.Agent.GrpcServer
{
    /// <summary>
    /// Experiment manager gRpc service.
    /// </summary>
    public class ExperimentManagerService : global::Mlos.ExperimentService.ExperimentManagerService.ExperimentManagerServiceBase
    {
        /// <summary>
        /// Gets or sets experiment session manager.
        /// </summary>
        public static ExperimentSessionManager ExperimentSessionManager { get; set; }

        public override Task<ExperimentAssemblyList> EnumerateAvailableExperiments(ExperimentAssemlyListRequest request, ServerCallContext context)
        {
            ExperimentAssemblyList reply = new ExperimentAssemblyList();

            reply.ExperimentAssemblyNames.AddRange(ExperimentSessionManager.AvailableExperimentAssemblies());
            return Task.FromResult(reply);
        }

        public override Task<LoadExperimentReply> LoadExperiment(LoadExperimentRequest request, ServerCallContext context)
        {
            LoadExperimentReply reply;

            try
            {
                ExperimentSessionManager.LoadExperiment(experimentAssemblyPath: request.ExperimentName);
                reply = new LoadExperimentReply
                {
                    Success = true,
                };
            }
            catch (Exception ex)
            {
                reply = new LoadExperimentReply
                {
                    Success = false,
                    ErrorMessage = ex.ToString(),
                };
            }

            return Task.FromResult(reply);
        }

        public override Task<StartExperimentReply> StartExperiment(StartExperimentRequest request, ServerCallContext context)
        {
            bool success = ExperimentSessionManager.StartExperiment(request.NumRandomIterations, request.NumGuidedIterations);
            StartExperimentReply reply = new StartExperimentReply();
            reply.Success = success;
            return Task.FromResult(reply);
        }

        public override Task<GetOptimizerIdReply> GetOptimizerId(GetOptimizerIdRequest request, ServerCallContext context)
        {
            GetOptimizerIdReply reply = new GetOptimizerIdReply();
            reply.OptimizerId = ExperimentSessionManager.GetOptimizerId();
            return Task.FromResult(reply);
        }

        public override Task<GetParameterSpaceReply> GetParameterSpace(GetParameterSpaceRequest request, ServerCallContext context)
        {
            GetParameterSpaceReply reply = new GetParameterSpaceReply();
            reply.ParameterSpaceJsonString = ExperimentSessionManager.GetParameterSpace(experimentName: request.ExperimentName);
            return Task.FromResult(reply);
        }

        public override Task<GetExperimentProgressReply> GetExperimentProgress(GetExperimentProgressRequest request, ServerCallContext context)
        {
            GetExperimentProgressReply reply = new GetExperimentProgressReply();
            reply.RemainingRandomIterations = (uint)ExperimentSessionManager.GetRemainingRandomIterations();
            reply.RemainingGuidedIterations = (uint)ExperimentSessionManager.GetRemainingGuidedIterations();
            return Task.FromResult(reply);
        }
    }
}
